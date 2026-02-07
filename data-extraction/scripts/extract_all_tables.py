#!/usr/bin/env python3
"""
全表自动提取：从 PDF 中完整且正确地提取每个表的数据并保存
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.pdf_extractor import PDFExtractor
from extractors.pdf_extractor_v2 import PDFExtractorV2
from processors.data_cleaner import DataCleaner
from processors.relationship_extractor import RelationshipExtractor
from processors.semantic_enricher import SemanticEnricher
from config import PDF_PATH, OUTPUT_DIR
from utils.logger import logger


def extract_all_tables():
    """提取所有表并保存"""
    logger.info("=" * 80)
    logger.info("GB 2760-2024 全表自动提取")
    logger.info("=" * 80)

    pdf_extractor = PDFExtractor(PDF_PATH)
    pdf_extractor_v2 = PDFExtractorV2(PDF_PATH)
    data_cleaner = DataCleaner()
    relationship_extractor = RelationshipExtractor()

    result = {
        "extracted_at": datetime.now().isoformat(),
        "source": str(PDF_PATH),
        "tables": {},
        "statistics": {},
        "relationships": {},
    }

    # ---------- 表 A.1：食品添加剂使用规定 ----------
    logger.info("\n[1/3] 提取表 A.1（食品添加剂使用规定）...")
    table_a1_raw = pdf_extractor_v2.extract_table_a1()
    table_a1_cleaned = [data_cleaner.clean_additive_data(row) for row in table_a1_raw]
    # 排除语义规范化：将「各类食品 表A.2 1~68 除外」等行转为正确结构化数据（food_category_code、food_name、exclusion_semantic）
    table_a1_normalized = [SemanticEnricher.normalize_a1_exclusion_row(row) for row in table_a1_cleaned]
    result["tables"]["A.1"] = table_a1_normalized
    result["statistics"]["A.1"] = len(table_a1_normalized)
    logger.info(f"  表 A.1 完成：{len(table_a1_normalized)} 条")

    # ---------- 表 A.2：例外食品编号 ----------
    logger.info("\n[2/3] 提取表 A.2（例外食品编号）...")
    table_a2_raw = pdf_extractor.extract_tables("A.2")
    table_a2_cleaned = list(table_a2_raw)  # A.2 保持原样，均为字典
    result["tables"]["A.2"] = table_a2_cleaned
    result["statistics"]["A.2"] = len(table_a2_cleaned)
    logger.info(f"  表 A.2 完成：{len(table_a2_cleaned)} 条")

    # ---------- 表 E.1：食品分类系统 ----------
    logger.info("\n[3/3] 提取表 E.1（食品分类系统）...")
    table_e1_raw = pdf_extractor.extract_tables("E.1")
    table_e1_cleaned = []
    for row in table_e1_raw:
        if isinstance(row, dict):
            cleaned = data_cleaner.clean_food_category_data(row)
        else:
            cleaned = row
        table_e1_cleaned.append(cleaned)
    result["tables"]["E.1"] = table_e1_cleaned
    result["statistics"]["E.1"] = len(table_e1_cleaned)
    logger.info(f"  表 E.1 完成：{len(table_e1_cleaned)} 条")

    # ---------- 关系提取 ----------
    logger.info("\n提取关系...")
    result["relationships"]["usage"] = relationship_extractor.extract_usage_relationships(table_a1_normalized)
    result["relationships"]["function"] = relationship_extractor.extract_function_relationships(table_a1_normalized)
    result["relationships"]["hierarchy"] = relationship_extractor.extract_category_hierarchy(table_e1_cleaned)
    result["relationships"]["exclusion"] = relationship_extractor.extract_exclusion_relationships(
        table_a2_cleaned, result["relationships"]["usage"]
    )
    result["relationships"]["mixing"] = relationship_extractor.extract_mixing_relationships(table_a1_normalized)
    for key, val in result["relationships"].items():
        result["statistics"][f"rel_{key}"] = len(val)
        logger.info(f"  关系 {key}: {len(val)} 条")

    # ---------- 保存 ----------
    out_file = OUTPUT_DIR / "all_tables_extracted.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"\n全部保存至: {out_file}")

    # 同时写一份精简版（仅统计与各表条数），便于快速查看
    report = {
        "extracted_at": result["extracted_at"],
        "statistics": result["statistics"],
        "output_file": str(out_file),
    }
    report_file = OUTPUT_DIR / "extraction_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"报告保存至: {report_file}")

    logger.info("\n" + "=" * 80)
    logger.info("全表提取完成")
    logger.info("=" * 80)
    return result


if __name__ == "__main__":
    extract_all_tables()
