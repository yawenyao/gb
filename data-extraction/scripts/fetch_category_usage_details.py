#!/usr/bin/env python3
"""
抓取每个食品分类的「使用详情」页（category/limit/{limit_id}.html），
解析：分类描述 + 本类允许的添加剂 / 上级类允许的 / 表A.2 GMP 三张表，
整理为 category_usage_details.json，便于复刻「按食品名称查询」。
"""
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup

from config import OUTPUT_DIR
from utils.logger import logger

BASE_URL = "https://2760.foodmate.net"
OUT_DIR = OUTPUT_DIR / "foodmate"
DELAY = 1.2
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
# 请求中文页面，便于解析「食品名称描述」和添加剂表


def get(url: str) -> Optional[str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except Exception as e:
        logger.warning("GET %s 失败: %s", url, e)
        return None


def _clean(t: str) -> str:
    return (t or "").replace("\u200b", "").strip()


def parse_limit_page(html: str, limit_id: int, category_code: str, category_name: str) -> Dict[str, Any]:
    """
    解析 limit 页：分类描述 + 三块添加剂表（本类 / 上级类 / 表A.2 GMP）。
    返回一条使用详情记录。
    """
    soup = BeautifulSoup(html, "html.parser")
    out = {
        "limit_id": limit_id,
        "category_code": category_code,
        "category_name": category_name,
        "category_name_en": "",
        "category_description": "",
        "additives_direct": [],
        "additives_parent": [],
        "additives_gmp": [],
    }

    # 1) 两列表格：分类号 / 食品名称 / 食品名称描述（中英文键名都可能）
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            key = _clean(tds[0].get_text()).lower()
            val = _clean(tds[1].get_text())
            if "food name" in key and "description" not in key:
                out["category_name_en"] = val
            elif "description" in key or "描述" in key or "食品名称描述" in (tds[0].get_text() or ""):
                out["category_description"] = val

    # 2) 按文档顺序：前三个「添加剂|功能|最大使用量|CNS|INS|备注」或英文表头表
    #    分别为：本类允许 / 上级类允许 / 表A.2 GMP
    def _is_usage_table(txt: str) -> bool:
        if "Additive" in txt and "Maximum" in txt:
            return True
        if "添加剂" in txt and ("最大使用" in txt or "CNS" in txt):
            return True
        return False

    tables = soup.find_all("table")
    section_index = 0
    section_keys = ["additives_direct", "additives_parent", "additives_gmp"]
    for table in tables:
        header_text = table.get_text()
        if not _is_usage_table(header_text):
            continue
        if section_index >= len(section_keys):
            break
        section = section_keys[section_index]
        section_index += 1
        rows = table.find_all("tr")
        for tr in rows[1:]:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            links = tr.find_all("a", href=re.compile(r"addtives/faid/(\d+)\.html"))
            faid = int(links[0]["href"].split("faid/")[1].split(".html")[0]) if links else None
            name_cn = _clean(links[0].get_text()) if links else _clean(tds[0].get_text())
            func = _clean(tds[1].get_text()) if len(tds) > 1 else ""
            max_usage = _clean(tds[2].get_text()) if len(tds) > 2 else ""
            cns = _clean(tds[3].get_text()) if len(tds) > 3 else ""
            ins = _clean(tds[4].get_text()) if len(tds) > 4 else ""
            remark = _clean(tds[5].get_text()) if len(tds) > 5 else ""
            if not name_cn and not faid:
                continue
            row = {
                "faid": faid,
                "name_cn": name_cn,
                "function": func or None,
                "max_usage": max_usage or None,
                "cns": cns or None,
                "ins": ins or None,
                "remark": remark or None,
            }
            out[section].append(row)

    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    categories_path = OUT_DIR / "categories.json"
    if not categories_path.exists():
        logger.error("请先运行 crawl_foodmate_2760.py 生成 categories.json")
        sys.exit(1)
    with open(categories_path, "r", encoding="utf-8") as f:
        categories = json.load(f)
    logger.info("共 %s 个食品分类，开始抓取使用详情页 ...", len(categories))

    details = []
    for i, cat in enumerate(categories):
        limit_id = cat.get("limit_id")
        if limit_id is None:
            continue
        url = f"{BASE_URL}/category/limit/{limit_id}.html"
        time.sleep(DELAY)
        html = get(url)
        if not html:
            details.append({
                "limit_id": limit_id,
                "category_code": cat.get("category_code", ""),
                "category_name": cat.get("category_name", ""),
                "category_name_en": "",
                "category_description": "",
                "additives_direct": [],
                "additives_parent": [],
                "additives_gmp": [],
            })
            continue
        detail = parse_limit_page(
            html,
            limit_id,
            cat.get("category_code", ""),
            cat.get("category_name", ""),
        )
        details.append(detail)
        if (i + 1) % 50 == 0:
            logger.info("   已处理 %s/%s", i + 1, len(categories))

    out_path = OUT_DIR / "category_usage_details.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    logger.info("已保存 %s（%s 条）", out_path.name, len(details))

    # 更新索引
    index_path = OUT_DIR / "crawl_index.json"
    if index_path.exists():
        idx = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        idx = {"source": BASE_URL, "files": []}
    idx["category_usage_details_count"] = len(details)
    idx["files"] = list(set(idx.get("files", [])) | {"category_usage_details.json"})
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    logger.info("完成。")


if __name__ == "__main__":
    main()
