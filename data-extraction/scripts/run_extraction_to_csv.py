#!/usr/bin/env python3
"""
一键流程：从 PDF 提取完整且正确的数据 → 导出为结构化 CSV（便于导入图数据库）。

步骤：
1. extract_all_tables.py  — 从 PDF 提取表 A.1 / A.2 / E.1，并做排除语义规范化
2. export_tables_to_csv.py — 将 all_tables_extracted.json 导出为 output/csv/*.csv

可选：format_tables_with_semantics.py 可再生成带引用/层级/聚合的格式化 JSON（output/formatted_tables/）。
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OUTPUT_DIR
from utils.logger import logger

EXTRACTED_JSON = OUTPUT_DIR / "all_tables_extracted.json"


def main():
    scripts_dir = Path(__file__).parent
    # 1. PDF 提取 + 规范化（难点与关键）
    logger.info("Step 1: PDF 提取与语义规范化 ...")
    r1 = subprocess.run(
        [sys.executable, str(scripts_dir / "extract_all_tables.py")],
        cwd=scripts_dir.parent,
    )
    if r1.returncode != 0:
        logger.error("提取失败，退出码 %s", r1.returncode)
        sys.exit(r1.returncode)
    if not EXTRACTED_JSON.exists():
        logger.error("未生成 %s", EXTRACTED_JSON)
        sys.exit(1)
    # 2. 导出 CSV
    logger.info("Step 2: 导出结构化 CSV ...")
    r2 = subprocess.run(
        [sys.executable, str(scripts_dir / "export_tables_to_csv.py")],
        cwd=scripts_dir.parent,
    )
    if r2.returncode != 0:
        logger.error("CSV 导出失败，退出码 %s", r2.returncode)
        sys.exit(r2.returncode)
    logger.info("完成：PDF → 正确数据 → CSV，可直接用于图数据库导入。")


if __name__ == "__main__":
    main()
