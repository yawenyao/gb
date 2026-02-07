#!/usr/bin/env python3
"""
由 additives_with_usage.json 构建「按添加剂查：哪些食品分类可用 + 使用细节」的索引 additive_usage_for_query.json。
key 为 faid（数字或字符串）及 cns（便于按 CNS 号查询），value 含该添加剂基本信息 + usage 列表（每条带 usage_type、residue_note）。
与 category_usage_for_query 形成双向闭环。
"""
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OUTPUT_DIR
from utils.logger import logger

OUT_DIR = OUTPUT_DIR / "foodmate"

APPROPRIATE_PATTERNS = [
    "按生产需要适量使用",
    "适量使用",
    "gmp",
    "proper level",
    "as needed",
]
RESIDUE_KEYWORDS = ["残留量", "残留", "residue"]


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


def main():
    p = OUT_DIR / "additives_with_usage.json"
    if not p.exists():
        logger.error("请先运行 crawl_foodmate_2760.py 生成 additives_with_usage.json")
        sys.exit(1)
    with open(p, "r", encoding="utf-8") as f:
        additives = json.load(f)

    by_faid: Dict[str, Dict[str, Any]] = {}
    by_cns: Dict[str, str] = {}  # cns -> faid (first occurrence)

    for a in additives:
        faid = a.get("faid")
        if faid is None:
            continue
        usage_list: List[Dict[str, Any]] = []
        for u in a.get("usage", []):
            usage_type, residue_note = _classify_usage_type(u.get("max_usage"), u.get("remark"))
            row = {
                "food_category_code": u.get("food_category_code"),
                "food_name": u.get("food_name"),
                "max_usage": u.get("max_usage"),
                "remark": u.get("remark"),
                "usage_type": usage_type,
            }
            if residue_note:
                row["residue_note"] = residue_note
            usage_list.append(row)

        entry = {
            "faid": faid,
            "name_cn": a.get("name_cn", ""),
            "name_en": a.get("name_en", ""),
            "cns": a.get("cns", ""),
            "ins": a.get("ins", ""),
            "function": a.get("function", ""),
            "usage": usage_list,
            "count_by_usage_type": {
                "最大使用量": sum(1 for u in usage_list if u.get("usage_type") == "最大使用量"),
                "按生产需要适量使用": sum(1 for u in usage_list if u.get("usage_type") == "按生产需要适量使用"),
                "残留量": sum(1 for u in usage_list if u.get("usage_type") == "残留量"),
            },
        }
        key = str(faid)
        by_faid[key] = entry
        cns = (a.get("cns") or "").strip()
        if cns and cns not in by_cns:
            by_cns[cns] = key

    out = {
        "_by_faid": by_faid,
        "_by_cns": by_cns,
        "_meta": {
            "description": "additive_usage_for_query: 按 faid 或 cns 查某添加剂在哪些食品分类可用及使用细节",
            "query_by_faid": "data._by_faid[faid]",
            "query_by_cns": "data._by_cns[cns] 得到 faid，再 data._by_faid[faid]",
        },
    }
    out_path = OUT_DIR / "additive_usage_for_query.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    logger.info("已生成 %s（%s 个添加剂，支持按 faid / cns 查询）", out_path.name, len(by_faid))

    idx_path = OUT_DIR / "crawl_index.json"
    if idx_path.exists():
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
    else:
        idx = {}
    idx["files"] = list(set(idx.get("files", [])) | {"additive_usage_for_query.json"})
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    logger.info("完成。")


if __name__ == "__main__":
    main()
