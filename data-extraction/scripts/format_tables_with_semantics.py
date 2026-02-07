#!/usr/bin/env python3
"""
按表整理出完整、正确的格式化数据集，并包含 引用、嵌套、层级、聚合、排斥 等语义字段。
输出：每个表一个独立的结构化 JSON 文件 + 一份汇总说明。
"""
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.pdf_extractor import PDFExtractor
from extractors.pdf_extractor_v2 import PDFExtractorV2
from processors.data_cleaner import DataCleaner
from processors.relationship_extractor import RelationshipExtractor
from processors.semantic_enricher import SemanticEnricher, build_e1_nested
from config import PDF_PATH, OUTPUT_DIR
from utils.logger import logger


def normalize_food_category_code(row: Dict[str, Any]) -> str:
    """
    规范化食品分类号：若为“各类食品…除外”则返回特殊标识，便于与表E.1/A.2关联。
    """
    code = (row.get("food_category_code") or "").strip()
    if code and re.match(r"^\d+(\.\d+)*$", code):
        return code
    food_name = (row.get("food_name") or "").replace("\n", " ")
    if "各类食品" in food_name and "除外" in food_name:
        excl = SemanticEnricher.parse_exclusion_from_text(food_name)
        if excl and excl.get("exclusion_codes"):
            return f"ALL_EXCEPT_A2_{min(excl['exclusion_codes'])}-{max(excl['exclusion_codes'])}"
        return "ALL_EXCEPT_A2"
    return code or ""


def format_table_a1(
    table_a1_raw: List[Dict[str, Any]],
    data_cleaner: DataCleaner,
) -> Dict[str, Any]:
    """表A.1：完整格式化 + 引用/层级/聚合/排斥语义"""
    schema = {
        "table_id": "A.1",
        "name": "食品添加剂允许使用品种、使用范围及最大使用量或残留量",
        "fields": [
            "additive_name", "cns", "ins", "function",
            "food_category_code", "food_name", "max_usage", "unit", "note",
            "semantic_references", "semantic_exclusion", "semantic_aggregation", "semantic_hierarchy",
        ],
    }
    rows = []
    for row in table_a1_raw:
        cleaned = data_cleaner.clean_additive_data(row)
        enriched = SemanticEnricher.enrich_a1_row(cleaned)
        # 规范化分类号（便于关联）
        enriched["food_category_code_normalized"] = normalize_food_category_code(enriched)
        rows.append(enriched)
    return {
        "schema": schema,
        "semantic_notes": [
            "semantic_references: 引用（按…规定、参照、以…计、表A.2等）",
            "semantic_exclusion: 排斥（表A.2中编号xxx除外）",
            "semantic_aggregation: 聚合（各类食品等）",
            "semantic_hierarchy: 层级（由食品分类号推导的 parent/level）",
        ],
        "row_count": len(rows),
        "rows": rows,
    }


def format_table_a2(table_a2_raw: List[Dict[str, Any]]) -> Dict[str, Any]:
    """表A.2：例外食品编号 — 完整格式化，含层级（与E.1的对应关系）"""
    schema = {
        "table_id": "A.2",
        "name": "表A.1中例外食品编号对应的食品类别",
        "fields": ["exception_code", "food_category_code", "food_name", "page", "source"],
    }
    rows = []
    for row in table_a2_raw:
        code = row.get("exception_code") or row.get("serial_number") or ""
        # 清洗编号：如 "1." -> "1"
        code = re.sub(r"^\s*(\d+)\s*\.?\s*$", r"\1", str(code).strip())
        fc = (row.get("food_category_code") or "").strip()
        name = (row.get("food_name") or row.get("category_name") or "").strip()
        rows.append({
            "exception_code": code,
            "food_category_code": fc,
            "food_name": name,
            "page": row.get("page"),
            "source": row.get("source", "PDF"),
    })
    return {
        "schema": schema,
        "semantic_notes": [
            "exception_code 对应表A.1中“表A.2中编号xxx除外”的编号，用于关联A.1与A.2",
        ],
        "row_count": len(rows),
        "rows": rows,
    }


def format_table_e1(
    table_e1_raw: List[Dict[str, Any]],
    data_cleaner: DataCleaner,
) -> Dict[str, Any]:
    """表E.1：食品分类系统 — 扁平表 + 嵌套树，含层级与父子关系"""
    cleaned = []
    for row in table_e1_raw:
        c = data_cleaner.clean_food_category_data(row)
        c = SemanticEnricher.enrich_e1_row(c)
        cleaned.append(c)
    nested = build_e1_nested(cleaned)
    schema = {
        "table_id": "E.1",
        "name": "食品分类系统",
        "fields": ["category_code", "category_name", "level", "parent_code", "children"],
    }
    return {
        "schema": schema,
        "semantic_notes": [
            "level: 由分类号点数推导的层级；parent_code: 父分类号；children: 子节点（嵌套）",
        ],
        "row_count": len(cleaned),
        "rows_flat": cleaned,
        "rows_nested": nested,
    }


def main():
    logger.info("=" * 80)
    logger.info("各表完整格式化（含引用/嵌套/层级/聚合/排斥语义）")
    logger.info("=" * 80)

    pdf_extractor = PDFExtractor(PDF_PATH)
    pdf_extractor_v2 = PDFExtractorV2(PDF_PATH)
    data_cleaner = DataCleaner()
    relationship_extractor = RelationshipExtractor()

    # ---------- 提取原始数据 ----------
    logger.info("\n提取表 A.1...")
    table_a1_raw = pdf_extractor_v2.extract_table_a1()
    logger.info("提取表 A.2...")
    table_a2_raw = pdf_extractor.extract_tables("A.2")
    logger.info("提取表 E.1...")
    table_e1_raw = pdf_extractor.extract_tables("E.1")

    # ---------- 格式化 + 语义增强 ----------
    logger.info("\n格式化 表A.1（含引用/层级/聚合/排斥）...")
    formatted_a1 = format_table_a1(table_a1_raw, data_cleaner)
    logger.info("格式化 表A.2...")
    formatted_a2 = format_table_a2(table_a2_raw)
    logger.info("格式化 表E.1（含层级与嵌套）...")
    formatted_e1 = format_table_e1(table_e1_raw, data_cleaner)

    # ---------- 关系（供关联使用） ----------
    table_a1_cleaned = [data_cleaner.clean_additive_data(r) for r in table_a1_raw]
    table_e1_cleaned = [data_cleaner.clean_food_category_data(r) for r in table_e1_raw]
    usage_rel = relationship_extractor.extract_usage_relationships(table_a1_cleaned)
    hierarchy_rel = relationship_extractor.extract_category_hierarchy(table_e1_cleaned)

    # ---------- 写出每个表的独立文件 ----------
    out_dir = OUTPUT_DIR / "formatted_tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    def write_json(name: str, data: Dict[str, Any]) -> Path:
        path = out_dir / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"  已写: {path}")
        return path

    write_json("table_A1_formatted.json", formatted_a1)
    write_json("table_A2_formatted.json", formatted_a2)
    write_json("table_E1_formatted.json", formatted_e1)

    # ---------- 汇总与语义关系索引 ----------
    summary = {
        "generated_at": datetime.now().isoformat(),
        "source_pdf": str(PDF_PATH),
        "tables": {
            "A.1": {
                "row_count": formatted_a1["row_count"],
                "file": "formatted_tables/table_A1_formatted.json",
                "semantics": ["reference", "exclusion", "aggregation", "hierarchy"],
            },
            "A.2": {
                "row_count": formatted_a2["row_count"],
                "file": "formatted_tables/table_A2_formatted.json",
                "semantics": ["exception_code → A.1 exclusion"],
            },
            "E.1": {
                "row_count": formatted_e1["row_count"],
                "file": "formatted_tables/table_E1_formatted.json",
                "semantics": ["hierarchy", "nested (parent_code, children)"],
            },
        },
        "relationships": {
            "usage_count": len(usage_rel),
            "hierarchy_count": len(hierarchy_rel),
        },
    }
    write_json("formatted_tables_index.json", summary)
    # 索引放在 output 根下便于查找
    index_path = OUTPUT_DIR / "formatted_tables_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    logger.info(f"  索引: {index_path}")

    logger.info("\n" + "=" * 80)
    logger.info("完成：每个表已整理为完整、正确的格式化数据集（含语义）")
    logger.info("=" * 80)
    return summary


if __name__ == "__main__":
    main()
