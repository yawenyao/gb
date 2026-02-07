#!/usr/bin/env python3
"""
将 output/foodmate 下的爬取数据整理为「基础数据集」，输出到 output/foodmate_dataset/。
目录结构：
  entities/      - 实体表：additives, categories
  relations/     - 关系表：additive_usage（扁平，每条一行）
  reference/     - 附录与参考：加工助剂、酶制剂、香精香料、附录D、使用原则
  index/         - 查询索引：by_additive, by_category
  README.md, manifest.json
"""
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OUTPUT_DIR
from utils.logger import logger

SRC = OUTPUT_DIR / "foodmate"
DST = OUTPUT_DIR / "foodmate_dataset"

APPROPRIATE_PATTERNS = [
    "按生产需要适量使用",
    "适量使用",
    "gmp",
    "proper level",
    "as needed",
]
RESIDUE_KEYWORDS = ["残留量", "残留", "residue"]

# 最大使用量中已包含单位的模式（不含则按 GB 2760 表 A.1 默认 g/kg 补全）
UNIT_PATTERN = re.compile(
    r"(g|mg)/(kg|L|dm\s*\^?\s*2)|%|mL/kg|以残留量计|残留量\s*[≤<]",
    re.I
)
# 从 max_usage 字符串中提取第一个单位（用于关系属性 unit，便于展示/筛选）
UNIT_EXTRACT = re.compile(
    r"(?:(g|mg)/(kg|L|dm\s*\^?\s*2)|%|mL/kg)",
    re.I
)


def _normalize_max_usage(max_usage: Optional[str], usage_type: str) -> str:
    """对最大使用量补全单位：表 A.1 默认 g/kg；已有 g/kg/g/L 等则不动；带括号/条件的数值在数字后补 g/kg。"""
    mu = (max_usage or "").strip()
    if not mu:
        return mu
    if UNIT_PATTERN.search(mu):
        return mu
    if any(p in mu.lower() or p in mu for p in APPROPRIATE_PATTERNS):
        return mu
    if any(k in mu for k in RESIDUE_KEYWORDS):
        return mu
    if usage_type != "最大使用量":
        return mu
    # 纯数字（可选小数）：整条仅数字时补 g/kg
    if re.match(r"^\d+\.?\d*\s*$", mu):
        return f"{mu} g/kg"
    # 数字后紧跟（、，、,、； 的：在该数字后补 g/kg（0.6g/L（ 这类已有单位的不会匹配，因中间是 g/L）
    # 例如 "0.025（仅限果味饮料）,0.02（果味饮料除外）" -> "0.025 g/kg（仅限果味饮料）,0.02 g/kg（果味饮料除外）"
    mu = re.sub(r"(\d+\.?\d*)\s*(?=（|，|,|；)", r"\1 g/kg ", mu)
    # 结尾为数字且整条尚无单位时，在末尾数字后补 g/kg
    if re.search(r"\d+\.?\d*\s*$", mu) and not re.search(r"g/kg|g/L|mg/kg", mu):
        mu = re.sub(r"(\d+\.?\d*)\s*$", r"\1 g/kg", mu)
    return mu


def _extract_unit(max_usage: Optional[str]) -> Optional[str]:
    """从 max_usage 中提取第一个单位字符串，如 g/kg、g/L、%；无则返回 None。"""
    if not (max_usage or "").strip():
        return None
    m = UNIT_EXTRACT.search(max_usage)
    if not m:
        return None
    return m.group(0).strip()


def _parent_category_code(code: str, codes_set: set) -> Optional[str]:
    """由 category_code 推导父分类 code（用于层级）。如 01.05.03 -> 01.05；01.05 -> 01.0；01.0 -> None。"""
    if not code or "." not in code:
        return None
    parts = code.split(".")
    parent = ".".join(parts[:-1])
    if parent in codes_set and parent != code:
        return parent
    # 如 01.01 的父应为 01.0（列表中无 01）
    alt = parent + ".0"
    if alt in codes_set and alt != code:
        return alt
    return None


def _classify_usage_type(max_usage: Optional[str], remark: Optional[str]) -> Tuple[str, Optional[str]]:
    mu = (max_usage or "").strip()
    rm = (remark or "").strip()
    combined = f"{mu} {rm}"
    has_residue = any(k in combined for k in RESIDUE_KEYWORDS)
    residue_note = rm if (has_residue and rm) else (mu if (has_residue and mu and any(k in mu for k in RESIDUE_KEYWORDS)) else None)
    if has_residue and (
        re.search(r"残留量\s*[≤<]|残留\s*[≤<]|residue.*≤", combined, re.I)
        or (mu and "残留" in mu and not re.search(r"^\d+\.?\d*\s*(g|mg)/kg", mu))
    ):
        return ("残留量", residue_note)
    mu_lower = mu.lower()
    if any(p in mu_lower or p in mu for p in APPROPRIATE_PATTERNS):
        return ("按生产需要适量使用", residue_note)
    if mu and (
        re.match(r"^\d+\.?\d*\s*$", mu)
        or re.search(r"\d+\.?\d*\s*(g|mg)/kg", mu, re.I)
        or re.search(r"\d+\.?\d*\s*mg/dm", mu, re.I)
        or re.search(r"≤\s*\d+", mu)
    ):
        return ("最大使用量", residue_note)
    if mu:
        return ("最大使用量", residue_note)
    return ("按生产需要适量使用", residue_note)


def load(name: str) -> Any:
    p = SRC / name
    if not p.exists():
        raise FileNotFoundError(p)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_by_additive_index(data: Dict[str, Any]) -> None:
    """就地为 by_additive 中每条 usage 的 max_usage 补全单位。"""
    for entry in data.values():
        if not isinstance(entry, dict):
            continue
        for u in entry.get("usage") or []:
            if isinstance(u, dict) and "max_usage" in u:
                u["max_usage"] = _normalize_max_usage(
                    u.get("max_usage"), u.get("usage_type") or "最大使用量"
                )


def _normalize_by_category_index(data: Dict[str, Any]) -> None:
    """就地为 by_category 中每条 additive 的 max_usage 补全单位。"""
    for entry in data.values():
        if not isinstance(entry, dict):
            continue
        for a in entry.get("additives") or []:
            if isinstance(a, dict) and "max_usage" in a:
                a["max_usage"] = _normalize_max_usage(
                    a.get("max_usage"), a.get("usage_type") or "最大使用量"
                )


def main():
    if not SRC.exists():
        logger.error("请先完成 foodmate 爬取，确保 output/foodmate 存在")
        sys.exit(1)
    DST.mkdir(parents=True, exist_ok=True)
    (DST / "entities").mkdir(exist_ok=True)
    (DST / "relations").mkdir(exist_ok=True)
    (DST / "reference").mkdir(exist_ok=True)
    (DST / "index").mkdir(exist_ok=True)

    manifest = {"source": "https://2760.foodmate.net", "generated_from": "output/foodmate", "files": {}}

    # --- entities ---
    additives = load("additives.json")
    out_additives = []
    for a in additives:
        out_additives.append({
            "faid": a.get("id") or a.get("faid"),
            "name_cn": a.get("name_cn", ""),
            "name_en": a.get("name_en", ""),
            "cns": a.get("cns", ""),
            "ins": a.get("ins", ""),
            "function": a.get("function", ""),
        })
    save_json(DST / "entities" / "additives.json", out_additives)
    manifest["files"]["entities/additives.json"] = {"rows": len(out_additives), "description": "添加剂主表"}

    categories = load("categories.json")
    codes_set = {c.get("category_code", "") for c in categories if c.get("category_code")}
    out_categories = []
    for c in categories:
        code = c.get("category_code", "")
        out_categories.append({
            "category_code": code,
            "category_name": c.get("category_name", ""),
            "limit_id": c.get("limit_id"),
            "parent_category_code": _parent_category_code(code, codes_set),
        })
    save_json(DST / "entities" / "categories.json", out_categories)
    manifest["files"]["entities/categories.json"] = {"rows": len(out_categories), "description": "食品分类主表"}

    # --- 本级/上级/GMP 来源：从 category_usage_for_query 建 (category_code, faid) -> source ---
    by_category = load("category_usage_for_query.json")
    source_lookup: Dict[Tuple[str, int], str] = {}
    if isinstance(by_category, dict):
        for cat_code, entry in by_category.items():
            if not isinstance(entry, dict):
                continue
            for add in entry.get("additives") or []:
                if isinstance(add, dict) and "faid" in add and "source" in add:
                    source_lookup[(cat_code, int(add["faid"]))] = add["source"]

    # --- relations: additive_usage 扁平表（含 source、unit）---
    with_usage = load("additives_with_usage.json")
    flat_usage = []
    for a in with_usage:
        faid = a.get("faid")
        if faid is None:
            continue
        faid = int(faid)
        for u in a.get("usage", []):
            usage_type, residue_note = _classify_usage_type(u.get("max_usage"), u.get("remark"))
            raw_max = u.get("max_usage")
            max_usage_display = _normalize_max_usage(raw_max, usage_type)
            food_code = u.get("food_category_code")
            row = {
                "faid": faid,
                "food_category_code": food_code,
                "food_name": u.get("food_name"),
                "max_usage": max_usage_display,
                "remark": u.get("remark"),
                "usage_type": usage_type,
            }
            if residue_note:
                row["residue_note"] = residue_note
            source = source_lookup.get((food_code, faid))
            if source:
                row["source"] = source
            unit = _extract_unit(max_usage_display)
            if unit:
                row["unit"] = unit
            flat_usage.append(row)
    save_json(DST / "relations" / "additive_usage.json", flat_usage)
    manifest["files"]["relations/additive_usage.json"] = {"rows": len(flat_usage), "description": "添加剂-食品分类使用关系（扁平，每条一行）"}

    # --- reference ---
    for name, dst_name in [
        ("processing_aids.json", "processing_aids.json"),
        ("enzymes.json", "enzymes.json"),
        ("spices_b2_natural.json", "spices_b2_natural.json"),
        ("spices_b3_synthetic.json", "spices_b3_synthetic.json"),
        ("appendix_d_functions.json", "appendix_d_functions.json"),
        ("site_rules.json", "site_rules.json"),
    ]:
        data = load(name)
        save_json(DST / "reference" / dst_name, data)
        n = len(data) if isinstance(data, list) else 1
        manifest["files"][f"reference/{dst_name}"] = {"rows": n, "description": dst_name.replace(".json", "")}

    spices_rules = load("spices_rules.json")
    save_json(DST / "reference" / "spices_b1_prohibited.json", spices_rules.get("table_b1_prohibited", []))
    manifest["files"]["reference/spices_b1_prohibited.json"] = {"rows": len(spices_rules.get("table_b1_prohibited", [])), "description": "表B.1 不得添加香精香料的食品名单"}
    save_json(DST / "reference" / "spices_rules_principles.json", {"principles": spices_rules.get("principles", "")})
    manifest["files"]["reference/spices_rules_principles.json"] = {"rows": 1, "description": "香精香料使用原则正文"}

    # --- index（写入前对 max_usage 补全单位）---
    by_additive_raw = load("additive_usage_for_query.json")
    by_additive = by_additive_raw.get("_by_faid", by_additive_raw) if isinstance(by_additive_raw, dict) else by_additive_raw
    if isinstance(by_additive, dict):
        _normalize_by_additive_index(by_additive)
    save_json(DST / "index" / "by_additive.json", by_additive)
    n_add = len(by_additive) if isinstance(by_additive, dict) else 0
    manifest["files"]["index/by_additive.json"] = {"rows": n_add, "description": "按 faid 查添加剂可用分类及使用细节"}

    by_category = load("category_usage_for_query.json")
    if isinstance(by_category, dict):
        _normalize_by_category_index(by_category)
    save_json(DST / "index" / "by_category.json", by_category)
    manifest["files"]["index/by_category.json"] = {"rows": len(by_category), "description": "按 category_code 查该分类下可用添加剂及使用细则"}

    # --- README ---
    readme = """# GB 2760 食品添加剂基础数据集

数据来源：https://2760.foodmate.net ，经爬取与整理后形成本数据集，用于复刻查询、入库或二次开发。

## 目录结构

- **entities/** 实体表
  - `additives.json` 添加剂主表（faid, name_cn, name_en, cns, ins, function）
  - `categories.json` 食品分类主表（category_code, category_name, limit_id, parent_category_code 层级用）

- **relations/** 关系表
  - `additive_usage.json` 使用关系扁平表：每行一条「某添加剂在某食品分类下的使用规定」，含 faid, food_category_code, food_name, max_usage, remark, usage_type, residue_note；可选 source（本级/上级/GMP：direct/parent/gmp）、unit（从 max_usage 提取的单位）

- **reference/** 附录与参考
  - `processing_aids.json` 加工助剂
  - `enzymes.json` 酶制剂
  - `spices_b1_prohibited.json` 表B.1 不得添加香精香料的食品名单
  - `spices_b2_natural.json` 表B.2 食品用天然香料
  - `spices_b3_synthetic.json` 表B.3 食品用合成香料
  - `spices_rules_principles.json` 香精香料使用原则正文
  - `appendix_d_functions.json` 附录D 功能类别定义
  - `site_rules.json` 首页使用原则

- **index/** 查询索引（便于按添加剂或按分类快速查）
  - `by_additive.json` 按 faid 查：该添加剂在哪些食品分类可用及使用细节
  - `by_category.json` 按 category_code 查：该分类下可用添加剂及使用细则

## 使用方式

- **按添加剂查分类**：`index/by_additive.json[faid].usage`
- **按分类查添加剂**：`index/by_category.json[category_code].additives`
- **关系表统计/入库**：使用 `relations/additive_usage.json` 做分析或导入数据库

## manifest.json

记录各文件条数及说明，见 manifest.json。
"""
    (DST / "README.md").write_text(readme.strip(), encoding="utf-8")
    save_json(DST / "manifest.json", manifest)
    logger.info("基础数据集已写入 %s", DST)
    logger.info("  entities: additives %s, categories %s", len(out_additives), len(out_categories))
    logger.info("  relations: additive_usage %s", len(flat_usage))
    logger.info("  index: by_additive %s, by_category %s", n_add, len(by_category))


if __name__ == "__main__":
    main()
