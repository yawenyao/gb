"""
语义增强器：从文本中解析 引用、嵌套、层级、聚合、排斥 等语义，并附加到结构化数据上
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger


class SemanticEnricher:
    """语义增强器"""

    # 表A.2 中“例外食品编号”范围模式：允许 表…A.2…1-68…除外；除外前允许“食品”“类别”等
    RE_EXCLUSION_TABLE = re.compile(
        r"表\s*(?:.*?)\s*A\.?2\s*[^0-9]*?(\d+(?:\s*[~～\-、]\s*\d+)*)\s*[的]?(?:食品)?(?:类别)?\s*除外",
        re.I | re.DOTALL,
    )

    @staticmethod
    def _expand_code_range(s: str) -> List[int]:
        """将 '1~68' 或 '1~62、64~68' 展开为编号列表（用于与A.2对应）。仅做简单展开，不依赖A.2。"""
        s = s.strip()
        out: List[int] = []
        # 先匹配 数字~数字 或 数字-数字
        for m in re.finditer(r"(\d+)\s*[~～\-到至]\s*(\d+)", s):
            a, b = int(m.group(1)), int(m.group(2))
            for i in range(a, min(b + 1, 500)):
                out.append(i)
        # 再匹配单独数字（避免重复）
        for m in re.finditer(r"\b(\d+)\b", s):
            n = int(m.group(1))
            if n not in out:
                out.append(n)
        return sorted(set(out))

    @staticmethod
    def parse_exclusion_from_text(text: str) -> Optional[Dict[str, Any]]:
        """
        从“食品名称/备注”等文本解析排斥语义：表A.2中编号xxx的食品类别除外。
        返回: { "exclusion_ref": "A.2", "exclusion_codes": [1,2,...,68], "raw": "..." } 或 None
        """
        if not text:
            return None
        text_n = re.sub(r"\s+", " ", text)
        m = SemanticEnricher.RE_EXCLUSION_TABLE.search(text_n)
        if not m:
            # 宽松：表A.2 与 除外 之间的数字范围（避免把 A.2 里的 2 算进去）
            if "A.2" in text_n and "除外" in text_n:
                # 取 A.2 之后、除外 之前的片段再取数字（避免把 A.2 里的 2 算进编号）
                idx_a2 = text_n.find("A.2")
                idx_excl = text_n.rfind("除外")
                if idx_a2 < idx_excl:
                    segment = text_n[idx_a2 + 2 : idx_excl]
                    # 优先匹配范围：1-68 / 1~68 / 1~62、64~68，避免只匹配到单个数字
                    range_m = re.search(
                        r"(\d+)\s*[~～\-]\s*(\d+)(?:\s*[、,]\s*(\d+)\s*[~～\-]\s*(\d+))*",
                        segment,
                    )
                    if range_m:
                        # 至少有一组 低-高，展开所有范围（允许 ~/- 与第二数之间有少量非数字，如“64~ 的食品类别 68”）
                        codes = []
                        for part in re.finditer(
                            r"(\d+)\s*[~～\-]\s*(?:\s*\D*\s*)?(\d+)",
                            segment,
                        ):
                            a, b = int(part.group(1)), int(part.group(2))
                            codes.extend(range(a, min(b + 1, 500)))
                        codes = sorted(set(codes))
                        if codes:
                            return {
                                "exclusion_ref": "A.2",
                                "exclusion_codes": codes,
                                "raw": text_n[:200],
                            }
                    # 无范围时再匹配单个数字（如仅写“63”）
                    single_m = re.search(r"\b(\d+)\b", segment)
                    if single_m:
                        n = int(single_m.group(1))
                        if 1 <= n <= 100:
                            return {
                                "exclusion_ref": "A.2",
                                "exclusion_codes": [n],
                                "raw": text_n[:200],
                            }
            return None
        range_str = m.group(1).strip()  # e.g. "1-68" or "1~62、64~68"
        codes = SemanticEnricher._expand_code_range(range_str)
        if not codes:
            return None
        return {
            "exclusion_ref": "A.2",
            "exclusion_codes": codes,
            "raw": text_n[:200],
        }

    @staticmethod
    def _format_exclusion_codes_for_display(codes: List[int]) -> str:
        """将编号列表格式化为简短范围描述，如 1-68 或 1-62、64-68"""
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
        return "、".join(parts)

    @staticmethod
    def normalize_a1_exclusion_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        若该行为「各类食品 表A.2 xxx 除外」的排除语义，则补全为正确结构化数据：
        - food_category_code: 规范编码（如 ALL_EXCEPT_A2_1-68）
        - food_name: 规范描述（如 各类食品（表A.2中编号1-68的食品类别除外））
        - exclusion_semantic: { "exclusion_ref": "A.2", "exclusion_codes": [1..68] }
        返回新字典，不修改原 row。
        """
        out = dict(row)
        food_name_raw = (row.get("food_name") or "").replace("\n", " ").strip()
        note_raw = (row.get("note") or "").strip()
        text = f"{food_name_raw} {note_raw}"
        code = (row.get("food_category_code") or "").strip()
        # 判定为排除语义：食品名/备注含「各类食品」+「除外」+「A.2」，且多为空分类号或非具体分类号
        is_likely_exclusion = (
            ("各类食品" in text or "所有食品" in text)
            and "除外" in text
            and "A.2" in text
        )
        if not is_likely_exclusion:
            return out
        excl = SemanticEnricher.parse_exclusion_from_text(text)
        if not excl or not excl.get("exclusion_codes"):
            return out
        codes = excl["exclusion_codes"]
        range_str = SemanticEnricher._format_exclusion_codes_for_display(codes)
        out["food_category_code"] = f"ALL_EXCEPT_A2_{range_str.replace('、', '_')}"
        out["food_name"] = f"各类食品（表A.2中编号{range_str}的食品类别除外）"
        out["exclusion_semantic"] = {
            "exclusion_ref": excl.get("exclusion_ref", "A.2"),
            "exclusion_codes": codes,
        }
        return out

    @staticmethod
    def parse_aggregation_from_text(text: str) -> Optional[Dict[str, Any]]:
        """
        解析聚合语义：如“各类食品”表示范围是全部类别（可能再配合排斥）。
        返回: { "aggregation": True, "scope": "各类食品", "raw": "..." } 或 None
        """
        if not text:
            return None
        text_n = re.sub(r"\s+", " ", text).strip()
        if "各类食品" in text_n or "所有食品" in text_n:
            return {
                "aggregation": True,
                "scope": "各类食品" if "各类食品" in text_n else "所有食品",
                "raw": text_n[:200],
            }
        return None

    @staticmethod
    def parse_references_from_text(text: str) -> List[Dict[str, Any]]:
        """
        解析引用语义：按…规定、参照…、以…计、表A.2 等。
        返回: [ { "ref_type": "规定|参照|以计|表", "target": "..." }, ... ]
        """
        if not text:
            return []
        text_n = re.sub(r"\s+", " ", text)
        refs = []

        # 按…规定 / 依据… / 参照…
        for pattern, ref_type in [
            (r"按\s*([^，,。规定]+)\s*规定", "规定"),
            (r"依据\s*([^，,。]+?)(?:\.|$|\s)", "依据"),
            (r"参照\s*([^，,。]+?)(?:\.|$|\s)", "参照"),
        ]:
            for m in re.finditer(pattern, text_n):
                refs.append({"ref_type": ref_type, "target": m.group(1).strip()})

        # 以…计（如 以抗坏血酸计）
        for m in re.finditer(r"以\s*([^，,。]+?)\s*计", text_n):
            refs.append({"ref_type": "以计", "target": m.group(1).strip()})

        # 表A.2、表E.1 等
        for m in re.finditer(r"表\s*([A-E]\.?\d+)", text_n, re.I):
            refs.append({"ref_type": "表", "target": m.group(1).strip()})

        return refs

    @staticmethod
    def enrich_a1_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        对表A.1的一行做语义增强，增加 reference, exclusion, aggregation, hierarchy 等字段。
        """
        out = dict(row)
        food_name = (row.get("food_name") or "") + " " + (row.get("note") or "")
        note = row.get("note") or ""

        # 排斥
        excl = SemanticEnricher.parse_exclusion_from_text(food_name)
        if excl:
            out["semantic_exclusion"] = excl
            out["is_aggregation_with_exclusion"] = True
        else:
            out["semantic_exclusion"] = None
            out["is_aggregation_with_exclusion"] = False

        # 聚合
        agg = SemanticEnricher.parse_aggregation_from_text(food_name)
        if agg:
            out["semantic_aggregation"] = agg
        else:
            out["semantic_aggregation"] = None

        # 引用（从备注和食品名称）
        refs = SemanticEnricher.parse_references_from_text(note)
        refs += SemanticEnricher.parse_references_from_text(row.get("food_name") or "")
        out["semantic_references"] = refs if refs else []

        # 层级：由食品分类号推导
        code = (row.get("food_category_code") or "").strip()
        if code and re.match(r"^\d+(\.\d+)*$", code):
            level = code.count(".") + 1
            parent = code.rsplit(".", 1)[0] if "." in code else None
            out["semantic_hierarchy"] = {
                "category_code": code,
                "level": level,
                "parent_code": parent,
            }
        else:
            out["semantic_hierarchy"] = None

        return out

    @staticmethod
    def enrich_e1_row(row: Dict[str, Any], parent_code: Optional[str] = None) -> Dict[str, Any]:
        """对表E.1的一行做层级/嵌套语义增强。"""
        out = dict(row)
        code = row.get("category_code") or row.get("food_category_code") or ""
        code = re.sub(r"[^\d.]", "", code)
        if not code:
            out["semantic_hierarchy"] = None
            return out
        level = code.count(".") + 1
        parent = parent_code or (code.rsplit(".", 1)[0] if "." in code else None)
        out["semantic_hierarchy"] = {
            "category_code": code,
            "level": level,
            "parent_code": parent,
        }
        out["category_code"] = code
        return out


def build_e1_nested(e1_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将表E.1扁平列表转为带嵌套的结构（每个节点可有 children 列表）。
    """
    by_code: Dict[str, Dict[str, Any]] = {}
    for row in e1_rows:
        code = row.get("category_code") or row.get("food_category_code") or ""
        code = re.sub(r"[^\d.]", "", code)
        if not code:
            continue
        node = {
            "category_code": code,
            "category_name": row.get("category_name") or row.get("food_name") or "",
            "level": row.get("level", code.count(".") + 1),
            "parent_code": row.get("parent_code"),
            "children": [],
            "source": row.get("source", "PDF"),
        }
        by_code[code] = node

    # 挂到父节点下
    roots: List[Dict[str, Any]] = []
    for code, node in sorted(by_code.items()):
        parent_code = node.get("parent_code")
        if not parent_code or parent_code not in by_code:
            roots.append(node)
        else:
            by_code[parent_code]["children"].append(node)

    # 子节点按 code 排序
    def sort_children(n: Dict[str, Any]) -> None:
        n["children"].sort(key=lambda x: x["category_code"])
        for c in n["children"]:
            sort_children(c)

    for r in roots:
        sort_children(r)
    roots.sort(key=lambda x: x["category_code"])
    return roots
