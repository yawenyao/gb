#!/usr/bin/env python3
"""
将「完整且正确」的表数据导出为结构化 CSV，便于导入图数据库。

数据来源：all_tables_extracted.json（已含排除语义规范化等）
输出目录：output/csv/
- table_A1.csv  表A.1 食品添加剂使用规定（扁平化，含 exclusion_ref / exclusion_codes_str）
- table_A2.csv  表A.2 例外食品编号
- table_E1.csv  表E.1 食品分类系统（层级）
- edges_usage.csv      边：添加剂-食品类别 使用关系
- edges_hierarchy.csv  边：食品分类 父子层级
- edges_function.csv   边：添加剂-功能
- edges_exclusion.csv  边：A.1 排除语义 → A.2 编号（用于图模型）
"""
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OUTPUT_DIR
from utils.logger import logger

CSV_DIR = OUTPUT_DIR / "csv"
EXTRACTED_JSON = OUTPUT_DIR / "all_tables_extracted.json"


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return "|".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return str(v).strip()


def _exclusion_codes_to_str(codes: List[int]) -> str:
    """将 [1,2,...,68] 转为简短形式 1-68 或 1-62,64-68"""
    if not codes:
        return ""
    codes = sorted(set(codes))
    parts = []
    i = 0
    while i < len(codes):
        start = codes[i]
        end = start
        while i + 1 < len(codes) and codes[i + 1] == codes[i] + 1:
            i += 1
            end = codes[i]
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}-{end}")
        i += 1
    return ",".join(parts)


def export_table_a1(rows: List[Dict[str, Any]], out_path: Path) -> int:
    """表A.1：扁平化导出，function 用 | 连接，exclusion_semantic 拆成列"""
    cols = [
        "row_id",
        "additive_name", "cns", "ins", "function",
        "food_category_code", "food_name", "max_usage", "unit", "note",
        "exclusion_ref", "exclusion_codes_str",
        "page", "source",
    ]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i, row in enumerate(rows, start=1):
            excl = row.get("exclusion_semantic") or {}
            codes = excl.get("exclusion_codes") or []
            w.writerow([
                i,
                _safe_str(row.get("additive_name")),
                _safe_str(row.get("cns")),
                _safe_str(row.get("ins")),
                _safe_str(row.get("function")),
                _safe_str(row.get("food_category_code")),
                _safe_str(row.get("food_name")),
                _safe_str(row.get("max_usage")),
                _safe_str(row.get("unit")),
                _safe_str(row.get("note")),
                _safe_str(excl.get("exclusion_ref")),
                _exclusion_codes_to_str(codes) if isinstance(codes, list) else _safe_str(codes),
                _safe_str(row.get("page")),
                _safe_str(row.get("source")),
            ])
    return len(rows)


def export_table_a2(rows: List[Dict[str, Any]], out_path: Path) -> int:
    """表A.2：例外食品编号，已是扁平结构；exception_code 规范为纯数字"""
    cols = ["exception_code", "food_category_code", "food_name", "page", "source"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in rows:
            code = _safe_str(row.get("exception_code")).rstrip(".")
            w.writerow([
                code,
                _safe_str(row.get("food_category_code")),
                _safe_str(row.get("food_name")),
                _safe_str(row.get("page")),
                _safe_str(row.get("source")),
            ])
    return len(rows)


def export_table_e1(rows: List[Dict[str, Any]], out_path: Path) -> int:
    """表E.1：食品分类系统，category_code / level / parent_code 便于建层级图"""
    cols = ["category_code", "category_name", "level", "parent_code", "page", "source"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in rows:
            w.writerow([
                _safe_str(row.get("category_code") or row.get("food_category_code")),
                _safe_str(row.get("category_name")),
                _safe_str(row.get("level")),
                _safe_str(row.get("parent_code")),
                _safe_str(row.get("page")),
                _safe_str(row.get("source")),
            ])
    return len(rows)


def export_edges_usage(rows: List[Dict[str, Any]], out_path: Path) -> int:
    """边：添加剂 -[USES]-> 食品类别（用于图数据库）"""
    cols = ["additive_name", "food_category_code", "food_name", "max_usage", "unit", "source"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in rows:
            w.writerow([
                _safe_str(row.get("additive_name")),
                _safe_str(row.get("food_category_code")),
                _safe_str(row.get("food_name")),
                _safe_str(row.get("max_usage")),
                _safe_str(row.get("unit")),
                _safe_str(row.get("source")),
            ])
    return len(rows)


def export_edges_hierarchy(rows: List[Dict[str, Any]], out_path: Path) -> int:
    """边：子分类 -[PARENT_OF]-> 父分类（child_code, parent_code）"""
    cols = ["child_code", "parent_code", "child_name", "level", "source"]
    count = 0
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in rows:
            child = _safe_str(row.get("category_code") or row.get("food_category_code"))
            parent = _safe_str(row.get("parent_code"))
            if not child:
                continue
            count += 1
            w.writerow([
                child,
                parent,
                _safe_str(row.get("category_name")),
                _safe_str(row.get("level")),
                _safe_str(row.get("source")),
            ])
    return count


def export_edges_function(a1_rows: List[Dict[str, Any]], out_path: Path) -> int:
    """边：添加剂 -[HAS_FUNCTION]-> 功能（一行添加剂-食品对应多个功能时拆成多行）"""
    cols = ["additive_name", "food_category_code", "function_name", "source"]
    count = 0
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in a1_rows:
            add_name = _safe_str(row.get("additive_name"))
            fc = _safe_str(row.get("food_category_code"))
            funcs = row.get("function")
            if isinstance(funcs, list):
                for fn in funcs:
                    w.writerow([add_name, fc, _safe_str(fn), _safe_str(row.get("source"))])
                    count += 1
            else:
                w.writerow([add_name, fc, _safe_str(funcs), _safe_str(row.get("source"))])
                count += 1
    return count


def export_edges_exclusion(a1_rows: List[Dict[str, Any]], out_path: Path) -> int:
    """边：A.1 排除语义 → A.2 例外编号（additive_name, food_category_code_normalized, exception_code）"""
    cols = ["additive_name", "food_category_code", "exclusion_ref", "exception_code", "source"]
    count = 0
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in a1_rows:
            excl = row.get("exclusion_semantic")
            if not excl or not excl.get("exclusion_codes"):
                continue
            add_name = _safe_str(row.get("additive_name"))
            fc = _safe_str(row.get("food_category_code"))
            ref = _safe_str(excl.get("exclusion_ref"))
            for code in excl.get("exclusion_codes") or []:
                w.writerow([add_name, fc, ref, str(code), _safe_str(row.get("source"))])
                count += 1
    return count


def main():
    if not EXTRACTED_JSON.exists():
        logger.error("未找到 %s，请先运行 scripts/extract_all_tables.py 完成 PDF 提取与规范化", EXTRACTED_JSON)
        sys.exit(1)

    CSV_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("正在加载 %s ...", EXTRACTED_JSON)
    with open(EXTRACTED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables = data.get("tables", {})
    a1 = tables.get("A.1", [])
    a2 = tables.get("A.2", [])
    e1 = tables.get("E.1", [])

    logger.info("导出 CSV 到 %s", CSV_DIR)

    n_a1 = export_table_a1(a1, CSV_DIR / "table_A1.csv")
    logger.info("  table_A1.csv: %s 行", n_a1)

    n_a2 = export_table_a2(a2, CSV_DIR / "table_A2.csv")
    logger.info("  table_A2.csv: %s 行", n_a2)

    n_e1 = export_table_e1(e1, CSV_DIR / "table_E1.csv")
    logger.info("  table_E1.csv: %s 行", n_e1)

    rel = data.get("relationships", {})
    usage = rel.get("usage", [])
    n_usage = export_edges_usage(usage, CSV_DIR / "edges_usage.csv")
    logger.info("  edges_usage.csv: %s 行", n_usage)

    n_hier = export_edges_hierarchy(e1, CSV_DIR / "edges_hierarchy.csv")
    logger.info("  edges_hierarchy.csv: %s 行", n_hier)

    n_func = export_edges_function(a1, CSV_DIR / "edges_function.csv")
    logger.info("  edges_function.csv: %s 行", n_func)

    n_excl = export_edges_exclusion(a1, CSV_DIR / "edges_exclusion.csv")
    logger.info("  edges_exclusion.csv: %s 行", n_excl)

    index = {
        "source": str(EXTRACTED_JSON),
        "csv_dir": str(CSV_DIR),
        "tables": {
            "table_A1.csv": n_a1,
            "table_A2.csv": n_a2,
            "table_E1.csv": n_e1,
        },
        "edges": {
            "edges_usage.csv": n_usage,
            "edges_hierarchy.csv": n_hier,
            "edges_function.csv": n_func,
            "edges_exclusion.csv": n_excl,
        },
    }
    index_path = CSV_DIR / "csv_export_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    logger.info("  索引: %s", str(index_path))
    logger.info("完成：所有表与边已导出为结构化 CSV，可用于图数据库导入。")


if __name__ == "__main__":
    main()
