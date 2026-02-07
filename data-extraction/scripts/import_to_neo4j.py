#!/usr/bin/env python3
"""
从 all_tables_extracted.json 构建图数据并导入 Neo4j。
需先启动 Neo4j：cd docker && docker compose up -d
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OUTPUT_DIR, NEO4J_URI, NEO4J_PASSWORD
from importers.graph_importer import GraphImporter
from utils.logger import logger

EXTRACTED_JSON = OUTPUT_DIR / "all_tables_extracted.json"


def build_import_payload(data: dict) -> dict:
    """将 all_tables_extracted 格式转为 GraphImporter.import_from_json 所需格式"""
    tables = data.get("tables", {})
    rel = data.get("relationships", {})

    # 添加剂：从 A.1 去重 (additive_name, cns, ins, function)
    seen = set()
    additives = []
    for row in tables.get("A.1", []):
        name = row.get("additive_name") or ""
        if not name or name in seen:
            continue
        seen.add(name)
        additives.append({
            "id": name,
            "additive_name": name,
            "name": name,
            "ins_number": row.get("ins"),
            "function": row.get("function") or [],
            "source": row.get("source", "PDF"),
        })

    # 食品类别：E.1 + A.2（A.2 的 food_category_code 也要有节点，便于 EXCLUDED_FROM 关联）
    food_categories = []
    for row in tables.get("E.1", []):
        code = row.get("category_code") or row.get("food_category_code") or ""
        if not code or len(code) > 50:  # 跳过合并单元格的畸形长码
            continue
        food_categories.append({
            "category_code": code,
            "food_category_code": code,
            "category_name": row.get("category_name") or "",
            "food_name": row.get("category_name"),
            "level": row.get("level"),
            "parent_code": row.get("parent_code"),
            "source": row.get("source", "PDF"),
        })
    for row in tables.get("A.2", []):
        code = (row.get("food_category_code") or "").strip()
        if not code:
            continue
        if not any(f.get("food_category_code") == code for f in food_categories):
            food_categories.append({
                "category_code": code,
                "food_category_code": code,
                "category_name": row.get("food_name") or "",
                "food_name": row.get("food_name"),
                "level": None,
                "parent_code": None,
                "source": row.get("source", "PDF"),
            })
    # 使用关系中出现的食品分类号（如 ALL_EXCEPT_A2_1-68）也建节点，避免 MERGE 失败
    for row in rel.get("usage", []):
        code = (row.get("food_category_code") or "").strip()
        if not code or any(f.get("food_category_code") == code for f in food_categories):
            continue
        food_categories.append({
            "category_code": code,
            "food_category_code": code,
            "category_name": row.get("food_name") or code,
            "food_name": row.get("food_name"),
            "level": None,
            "parent_code": None,
            "source": row.get("source", "PDF"),
        })

    # 使用关系：直接用 relationships.usage
    usage_relationships = list(rel.get("usage", []))

    # 功能关系：直接用 relationships.function
    function_relationships = list(rel.get("function", []))

    # 排除关系：A.1 中带 exclusion_semantic 的行 → 通过 exception_code 对应到 A.2 的 food_category_code
    exception_to_food_code = {}
    for row in tables.get("A.2", []):
        ec = str(row.get("exception_code") or "").strip().rstrip(".")
        fc = (row.get("food_category_code") or "").strip()
        if ec and fc:
            exception_to_food_code[ec] = fc
    exclusion_relationships = []
    for row in tables.get("A.1", []):
        excl = row.get("exclusion_semantic")
        if not excl or not excl.get("exclusion_codes"):
            continue
        add_name = row.get("additive_name") or ""
        for code in excl.get("exclusion_codes", []):
            food_code = exception_to_food_code.get(str(code))
            if food_code:
                exclusion_relationships.append({
                    "additive_id": add_name,
                    "additive_name": add_name,
                    "food_code": food_code,
                    "reason": "表A.2例外食品",
                    "source": row.get("source", "PDF"),
                })

    # 混合关系
    mixing_relationships = list(rel.get("mixing", []))

    return {
        "additives": additives,
        "food_categories": food_categories,
        "usage_relationships": usage_relationships,
        "function_relationships": function_relationships,
        "exclusion_relationships": exclusion_relationships,
        "mixing_relationships": mixing_relationships,
    }


def main():
    if not EXTRACTED_JSON.exists():
        logger.error("未找到 %s，请先运行 scripts/run_extraction_to_csv.py 或 extract_all_tables.py", EXTRACTED_JSON)
        sys.exit(1)
    logger.info("加载 %s ...", EXTRACTED_JSON)
    with open(EXTRACTED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    payload = build_import_payload(data)
    logger.info("添加剂 %s，食品类别 %s，使用关系 %s，功能关系 %s，排除关系 %s，混合关系 %s",
                len(payload["additives"]), len(payload["food_categories"]),
                len(payload["usage_relationships"]), len(payload["function_relationships"]),
                len(payload["exclusion_relationships"]), len(payload["mixing_relationships"]))
    importer = GraphImporter()
    try:
        importer.import_additives(payload["additives"])
        importer.import_food_categories(payload["food_categories"])
        importer.import_usage_relationships(payload["usage_relationships"])
        importer.import_function_relationships(payload["function_relationships"])
        if payload["exclusion_relationships"]:
            importer.import_exclusion_relationships(payload["exclusion_relationships"])
        if payload["mixing_relationships"]:
            importer.import_mixing_relationships(payload["mixing_relationships"])
        stats = importer.get_statistics()
        logger.info("导入完成。统计: %s", stats)
    finally:
        importer.close()


if __name__ == "__main__":
    main()
