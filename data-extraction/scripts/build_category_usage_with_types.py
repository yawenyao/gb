#!/usr/bin/env python3
"""
在 category_usage_details.json 基础上：
1. 为每条添加剂使用记录标注 usage_type：最大使用量 / 按生产需要适量使用 / 残留量
2. 提取残留量相关表述到 residue_note（若有）
3. 生成按 category_code 可查的 category_usage_for_query.json，便于「查询任意食品分类的添加剂使用规则」
"""
import json
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OUTPUT_DIR
from utils.logger import logger

OUT_DIR = OUTPUT_DIR / "foodmate"

# 可适量使用的表述（不区分大小写）
APPROPRIATE_PATTERNS = [
    "按生产需要适量使用",
    "适量使用",
    "gmp",
    "proper level",
    "as needed",
]

# 残留量相关
RESIDUE_KEYWORDS = ["残留量", "残留", "residue"]


def _classify_usage_type(max_usage: Optional[str], remark: Optional[str]) -> Tuple[str, Optional[str]]:
    """
    根据 max_usage 和 remark 判断使用类型，并提取残留量说明。
    返回 (usage_type, residue_note)
    usage_type: "最大使用量" | "按生产需要适量使用" | "残留量"
    """
    mu = (max_usage or "").strip()
    rm = (remark or "").strip()
    combined = f"{mu} {rm}"

    # 1) 是否含残留量表述
    has_residue = any(k in combined for k in RESIDUE_KEYWORDS)
    residue_note = None
    if has_residue and rm:
        residue_note = rm
    elif has_residue and mu and any(k in mu for k in RESIDUE_KEYWORDS):
        residue_note = mu

    # 2) 若整条主要是残留量限定（如「残留量≤0.1 g/kg」），归为残留量
    if has_residue and (
        re.search(r"残留量\s*[≤<]|残留\s*[≤<]|residue.*≤", combined, re.I)
        or (mu and "残留" in mu and not re.search(r"^\d+\.?\d*\s*(g|mg)/kg", mu))
    ):
        return ("残留量", residue_note)

    # 3) 按生产需要适量使用
    mu_lower = mu.lower()
    if any(p in mu_lower or p in mu for p in APPROPRIATE_PATTERNS):
        return ("按生产需要适量使用", residue_note)

    # 4) 数值型最大使用量（含 g/kg、mg/kg、mg/dm² 等）
    if mu and (
        re.match(r"^\d+\.?\d*\s*$", mu)
        or re.search(r"\d+\.?\d*\s*(g|mg)/kg", mu, re.I)
        or re.search(r"\d+\.?\d*\s*mg/dm", mu, re.I)
        or re.search(r"≤\s*\d+", mu)
    ):
        return ("最大使用量", residue_note)

    # 默认：有非空 max_usage 视为最大使用量，否则适量
    if mu:
        return ("最大使用量", residue_note)
    return ("按生产需要适量使用", residue_note)


def enrich_item(item: dict, source: str) -> dict:
    """为单条添加剂记录添加 usage_type、residue_note、source。"""
    max_usage = item.get("max_usage")
    remark = item.get("remark")
    usage_type, residue_note = _classify_usage_type(max_usage, remark)
    out = {**item, "usage_type": usage_type, "source": source}
    if residue_note:
        out["residue_note"] = residue_note
    return out


def main():
    p = OUT_DIR / "category_usage_details.json"
    if not p.exists():
        logger.error("请先运行 fetch_category_usage_details.py 生成 category_usage_details.json")
        sys.exit(1)

    with open(p, "r", encoding="utf-8") as f:
        details = json.load(f)

    # 1) 为每条记录标注 usage_type，写回原文件（保留三组，全部保留、允许交集）
    enriched = []
    for rec in details:
        new_rec = {
            "limit_id": rec["limit_id"],
            "category_code": rec["category_code"],
            "category_name": rec["category_name"],
            "category_name_en": rec.get("category_name_en", ""),
            "category_description": rec.get("category_description", ""),
            "additives_direct": [enrich_item(x, "direct") for x in rec.get("additives_direct", [])],
            "additives_parent": [enrich_item(x, "parent") for x in rec.get("additives_parent", [])],
            "additives_gmp": [enrich_item(x, "gmp") for x in rec.get("additives_gmp", [])],
        }
        enriched.append(new_rec)

    with open(p, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    logger.info("已为 category_usage_details.json 每条记录标注 usage_type 并写回")

    # 2) 生成按 category_code 可查的汇总：每个分类下「全部」添加剂（含来源与类型），便于查询
    by_code = {}
    for rec in enriched:
        code = rec["category_code"]
        # 合并三组，全部保留（允许同一条添加剂因来源不同出现多次）
        all_items = (
            rec["additives_direct"]
            + rec["additives_parent"]
            + rec["additives_gmp"]
        )
        by_code[code] = {
            "category_code": code,
            "category_name": rec["category_name"],
            "category_name_en": rec.get("category_name_en", ""),
            "category_description": rec.get("category_description", ""),
            "limit_id": rec["limit_id"],
            "additives": all_items,
            "count_by_usage_type": {
                "最大使用量": sum(1 for a in all_items if a.get("usage_type") == "最大使用量"),
                "按生产需要适量使用": sum(1 for a in all_items if a.get("usage_type") == "按生产需要适量使用"),
                "残留量": sum(1 for a in all_items if a.get("usage_type") == "残留量"),
            },
            "count_by_source": {
                "direct": len(rec["additives_direct"]),
                "parent": len(rec["additives_parent"]),
                "gmp": len(rec["additives_gmp"]),
            },
        }

    query_path = OUT_DIR / "category_usage_for_query.json"
    with open(query_path, "w", encoding="utf-8") as f:
        json.dump(by_code, f, ensure_ascii=False, indent=2)
    logger.info("已生成 %s（按 category_code 查询，共 %s 个分类）", query_path.name, len(by_code))

    # 3) 更新 crawl_index
    idx_path = OUT_DIR / "crawl_index.json"
    if idx_path.exists():
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
    else:
        idx = {}
    idx["files"] = list(set(idx.get("files", [])) | {"category_usage_for_query.json"})
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    logger.info("完成。")


if __name__ == "__main__":
    main()
