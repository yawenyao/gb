#!/usr/bin/env python3
"""
分析 output/foodmate_dataset 下九张表的数据完整性，输出报告。
检查项：主键唯一性、必填字段、外键引用、覆盖度、索引与实体表一致性。
"""
import json
from pathlib import Path
from collections import defaultdict

sys_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(sys_path))

from config import OUTPUT_DIR

DST = OUTPUT_DIR / "foodmate_dataset"


def load(name: str):
    p = DST / name
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    report = {"tables": {}, "cross_checks": [], "summary": {"complete": True, "issues": []}}
    DST = OUTPUT_DIR / "foodmate_dataset"
    if not DST.exists():
        print("output/foodmate_dataset 不存在，请先运行 build_foodmate_dataset.py")
        return

    # --- 1. additives ---
    additives = load("entities/additives.json")
    faids = [a.get("faid") for a in additives]
    faid_set = set(faids)
    issues = []
    if len(faids) != len(faid_set):
        issues.append("faid 存在重复")
    null_faid = [a for a in additives if a.get("faid") is None]
    if null_faid:
        issues.append(f"faid 为空: {len(null_faid)} 条")
    null_name = [a for a in additives if not (a.get("name_cn") or a.get("name_en"))]
    if null_name:
        issues.append(f"name_cn/name_en 均为空: {len(null_name)} 条")
    report["tables"]["additives"] = {
        "rows": len(additives),
        "expected_min": 292,
        "unique_faid": len(faid_set),
        "issues": issues,
        "complete": len(issues) == 0,
    }

    # --- 2. categories ---
    categories = load("entities/categories.json")
    codes = [c.get("category_code") for c in categories]
    code_set = set(c for c in codes if c)
    issues = []
    if len(codes) != len(code_set):
        issues.append("category_code 存在重复")
    null_code = [c for c in categories if not c.get("category_code")]
    if null_code:
        issues.append(f"category_code 为空: {len(null_code)} 条")
    report["tables"]["categories"] = {
        "rows": len(categories),
        "expected_min": 388,
        "unique_category_code": len(code_set),
        "issues": issues,
        "complete": len(issues) == 0,
    }

    # --- 3. additive_usage ---
    usage = load("relations/additive_usage.json")
    usage_faids = set(r.get("faid") for r in usage)
    usage_codes = set(r.get("food_category_code") for r in usage if r.get("food_category_code"))
    # 特殊码 "—" 表示「各类食品除外」等，不在 categories 里
    usage_codes.discard("—")
    usage_codes.discard("")
    issues = []
    missing_faid = usage_faids - faid_set
    if missing_faid:
        issues.append(f"additive_usage 中 faid 不在 additives 内: {len(missing_faid)} 个, 示例 {list(missing_faid)[:5]}")
    missing_code = usage_codes - code_set
    if missing_code:
        issues.append(f"additive_usage 中 food_category_code 不在 categories 内: {len(missing_code)} 个, 示例 {list(missing_code)[:10]}")
    add_without_usage = faid_set - usage_faids
    if add_without_usage:
        issues.append(f"additives 中无任何 usage 记录的 faid: {len(add_without_usage)} 个, 示例 {list(add_without_usage)[:5]}")
    report["tables"]["additive_usage"] = {
        "rows": len(usage),
        "unique_faid_in_usage": len(usage_faids),
        "unique_category_code_in_usage": len(usage_codes),
        "issues": issues,
        "complete": len(issues) == 0,
    }
    if issues:
        report["summary"]["issues"].extend([f"additive_usage: {i}" for i in issues])
    if add_without_usage:
        report["summary"]["complete"] = False

    # --- 4. reference 表：行数 + 必填字段 ---
    ref_checks = [
        ("reference/processing_aids.json", "processing_aids", ["name_cn", "name_en"], 118),
        ("reference/enzymes.json", "enzymes", ["name_cn", "name_en", "source"], 226),
        ("reference/spices_b1_prohibited.json", "spices_b1_prohibited", ["category_code", "category_name"], 29),
        ("reference/spices_b2_natural.json", "spices_b2_natural", ["name_cn", "name_en", "code_no"], 388),
        ("reference/spices_b3_synthetic.json", "spices_b3_synthetic", ["name_cn", "name_en", "code_no"], 1505),
        ("reference/appendix_d_functions.json", "appendix_d_functions", ["number", "function", "definition"], 23),
    ]
    for path, key, required_fields, expected_min in ref_checks:
        data = load(path)
        rows = len(data) if isinstance(data, list) else 0
        issues = []
        if rows < expected_min:
            issues.append(f"行数 {rows} < 预期约 {expected_min}")
        if isinstance(data, list) and data and required_fields:
            missing = []
            for i, row in enumerate(data):
                if not isinstance(row, dict):
                    missing.append(f"行{i} 非对象")
                    continue
                for f in required_fields:
                    if not row.get(f):
                        missing.append(f"行{i} 缺 {f}")
            if len(missing) > 20:
                issues.append(f"必填字段缺失: {len(missing)} 处, 示例 {missing[:5]}")
            elif missing:
                issues.append(f"必填字段缺失: {missing[:10]}")
        report["tables"][key] = {
            "rows": rows,
            "expected_min": expected_min,
            "issues": issues,
            "complete": len(issues) == 0,
        }
        if issues:
            report["summary"]["complete"] = False
            report["summary"]["issues"].extend([f"{key}: {i}" for i in issues])

    # --- 5. index 与实体表一致 ---
    by_add = load("index/by_additive.json")
    by_cat = load("index/by_category.json")
    index_faids = set(by_add.keys()) if isinstance(by_add, dict) else set()
    index_codes = set(by_cat.keys()) if isinstance(by_cat, dict) else set()
    # 统一为字符串比较（faid 在 index 里可能是 "1","2"）
    faid_set_str = set(str(x) for x in faid_set)
    issues_idx = []
    if faid_set_str and index_faids != faid_set_str:
        diff_add = faid_set_str - index_faids
        diff_idx = index_faids - faid_set_str
        if diff_add:
            issues_idx.append(f"by_additive 缺少 faid: {len(diff_add)} 个")
        if diff_idx:
            issues_idx.append(f"by_additive 多出 faid: {len(diff_idx)} 个")
    if code_set and index_codes != code_set:
        diff_cat = code_set - index_codes
        diff_idx = index_codes - code_set
        if diff_cat:
            issues_idx.append(f"by_category 缺少 category_code: {len(diff_cat)} 个")
        if diff_idx:
            issues_idx.append(f"by_category 多出 category_code: {len(diff_idx)} 个")
    report["cross_checks"].append({
        "name": "index_vs_entities",
        "by_additive_keys": len(index_faids),
        "by_category_keys": len(index_codes),
        "issues": issues_idx,
    })
    if issues_idx:
        report["summary"]["issues"].extend(issues_idx)
        report["summary"]["complete"] = False

    # --- 输出 ---
    out_path = DST / "completeness_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("=== 九张表数据完整性分析 ===\n")
    for name, t in report["tables"].items():
        status = "完整" if t.get("complete", True) else "存在问题"
        print(f"{name}: {t.get('rows', '—')} 行, {status}")
        for i in t.get("issues", []):
            print(f"  - {i}")
    print("\n--- 交叉检查 ---")
    for c in report["cross_checks"]:
        print(f"{c['name']}: {c.get('issues', ['通过'])}")
    print("\n--- 总结 ---")
    print(f"整体: {'完整' if report['summary']['complete'] else '存在缺失或异常'}")
    for i in report["summary"].get("issues", []):
        print(f"  - {i}")
    print(f"\n报告已写入 {out_path}")


if __name__ == "__main__":
    main()
