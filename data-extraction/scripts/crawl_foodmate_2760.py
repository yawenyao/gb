#!/usr/bin/env python3
"""
爬取 https://2760.foodmate.net/ 全站数据，保存为 JSON，便于导入自己的数据库。

模块：
1. 食品添加剂列表 addtives.html → additives.json
2. 每个添加剂详情 addtives/faid/{id}.html → additives_with_usage.json
3. 食品分类 category.html → categories.json
4. 加工助剂 processing.html → processing_aids.json
5. 酶制剂 enzyme.html → enzymes.json
6. 香精香料 spices.html + type/b2.html + type/b3.html → spices_*.json、表B.1 禁止名单
7. 首页使用原则 → site_rules.json

注意：请遵守网站 robots.txt 与使用条款；建议请求间隔 1～2 秒，勿并发过大。
"""
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup

from config import OUTPUT_DIR
from utils.logger import logger

BASE_URL = "https://2760.foodmate.net"
OUT_DIR = OUTPUT_DIR / "foodmate"
DELAY = 1.5  # 秒
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def get(url: str) -> Optional[str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except Exception as e:
        logger.warning("GET %s 失败: %s", url, e)
        return None


def parse_additive_list(html: str) -> List[Dict[str, Any]]:
    """解析 addtives.html 表格：中文名、英文名、CNS、INS、功能、详情链接"""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        links = tr.find_all("a", href=re.compile(r"addtives/faid/\d+\.html"))
        if not links:
            continue
        href = links[0].get("href", "")
        faid = re.search(r"faid/(\d+)\.html", href)
        id_ = int(faid.group(1)) if faid else 0
        # 列顺序多为：中文名、英文名、CNS、INS、Function
        name_cn = (tds[0].get_text(strip=True) or "").replace("\u200b", "")
        name_en = (tds[1].get_text(strip=True) or "").replace("\u200b", "")
        cns = (tds[2].get_text(strip=True) or "").replace("—", "").replace("&mdash;", "")
        ins = (tds[3].get_text(strip=True) or "").replace("—", "").replace("&mdash;", "")
        func = (tds[4].get_text(strip=True) or "").replace("\u200b", "")
        rows.append({
            "id": id_,
            "name_cn": name_cn,
            "name_en": name_en,
            "cns": cns,
            "ins": ins,
            "function": func,
            "detail_url": urljoin(BASE_URL, href),
        })
    return rows


def parse_additive_detail(html: str, faid: int) -> Dict[str, Any]:
    """解析添加剂详情页：基本信息 + 使用范围表（两类：各类食品除外 / 表A.2 中）"""
    soup = BeautifulSoup(html, "html.parser")
    info = {
        "faid": faid,
        "name_cn": "",
        "name_en": "",
        "cns": "",
        "ins": "",
        "function": "",
        "quality_specification": None,
        "jecfa_specification": None,
        "usage": [],
    }

    # 基本信息：表格 两列 Key | Value
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            key = tds[0].get_text(strip=True).lower()
            val = tds[1].get_text(strip=True).replace("\u200b", "")
            if "chinese" in key or "中文" in key:
                info["name_cn"] = val
            elif "english" in key or "英文" in key:
                info["name_en"] = val
            elif "cns" in key:
                info["cns"] = val.replace("—", "").replace("&mdash;", "")
            elif "ins" in key:
                info["ins"] = val.replace("—", "").replace("&mdash;", "")
            elif "function" in key or "功能" in key:
                info["function"] = val
            elif "quality" in key or "质量规格" in key or "规格" in key:
                info["quality_specification"] = val or None
            elif "jecfa" in key:
                info["jecfa_specification"] = val or None

    # 使用范围表：表格含 Food Category No. | Food Name | Maximum usage level | Remarks
    for table in soup.find_all("table"):
        header_text = table.get_text()
        if "Food Category" not in header_text and "食品分类" not in header_text and "Maximum" not in header_text and "最大使用" not in header_text:
            continue
        rows = table.find_all("tr")
        for tr in rows[1:]:  # 跳过表头
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            links = tr.find_all("a", href=re.compile(r"category/limit/\d+\.html"))
            code = ""
            name = ""
            if links:
                code_cell = links[0]
                code = code_cell.get_text(strip=True)
                name = (tds[1].get_text(strip=True) if len(tds) > 1 else "").replace("\u200b", "")
            else:
                code = tds[0].get_text(strip=True)
                name = tds[1].get_text(strip=True) if len(tds) > 1 else ""
            max_usage = (tds[2].get_text(strip=True) if len(tds) > 2 else "").replace("\u200b", "")
            remark = (tds[3].get_text(strip=True) if len(tds) > 3 else "").replace("\u200b", "")
            if code or name:
                info["usage"].append({
                    "food_category_code": code,
                    "food_name": name,
                    "max_usage": max_usage or None,
                    "remark": remark or None,
                })
    return info


def parse_category_list(html: str) -> List[Dict[str, Any]]:
    """解析 category.html：食品分类号、名称、详情链接"""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        links = tr.find_all("a", href=re.compile(r"category/limit/\d+\.html"))
        if not links:
            continue
        href = links[0].get("href", "")
        code = (tds[0].get_text(strip=True) or "").replace("\u200b", "")
        name = (tds[1].get_text(strip=True) or "").replace("\u200b", "")
        limit_id = re.search(r"limit/(\d+)\.html", href)
        rows.append({
            "category_code": code,
            "category_name": name,
            "limit_id": int(limit_id.group(1)) if limit_id else None,
            "url": urljoin(BASE_URL, href),
        })
    return rows


def parse_processing_list(html: str) -> List[Dict[str, Any]]:
    """解析 processing.html：加工助剂表 中文名、英文名、功能、使用范围"""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        text = tr.get_text()
        if "Chinese Name" in text and "English Name" in text:
            continue
        name_cn = (tds[0].get_text(strip=True) or "").replace("\u200b", "")
        name_en = (tds[1].get_text(strip=True) or "").replace("\u200b", "")
        func = (tds[2].get_text(strip=True) or "").replace("\u200b", "")
        usage = (tds[3].get_text(strip=True) or "").replace("\u200b", "")
        if name_cn or name_en:
            rows.append({"name_cn": name_cn, "name_en": name_en, "function": func, "usage_scope": usage})
    return rows


def parse_enzyme_list(html: str) -> List[Dict[str, Any]]:
    """解析 enzyme.html：酶制剂表 中文名、英文名、来源、供体、备注"""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        text = tr.get_text()
        if "Chinese Name" in text and "Source" in text:
            continue
        name_cn = (tds[0].get_text(strip=True) or "").replace("\u200b", "")
        name_en = (tds[1].get_text(strip=True) or "").replace("\u200b", "")
        source = (tds[2].get_text(strip=True) or "").replace("\u200b", "")
        donor = (tds[3].get_text(strip=True) or "").replace("\u200b", "") if len(tds) > 3 else ""
        remark = (tds[4].get_text(strip=True) or "").replace("\u200b", "") if len(tds) > 4 else ""
        if name_cn or name_en or source:
            rows.append({"name_cn": name_cn, "name_en": name_en, "source": source, "donor": donor, "remarks": remark})
    return rows


def parse_spices_page(html: str) -> Dict[str, Any]:
    """解析 spices.html：使用原则正文 + 表 B.1 禁止添加香精香料的食品名单"""
    soup = BeautifulSoup(html, "html.parser")
    out = {"principles": "", "table_b1_prohibited": []}
    # 原则：取主内容区文本（含 B Principles、1.1～1.8 等）
    main = soup.find("div", class_=re.compile(r"content|main|body", re.I)) or soup.find("body")
    if main:
        out["principles"] = main.get_text(separator="\n", strip=True)[:12000]
    # 表 B.1：通常为 01.01.01|Pasteurized milk| 或两列
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                code = (tds[0].get_text(strip=True) or "").replace("\u200b", "")
                name = (tds[1].get_text(strip=True) or "").replace("\u200b", "")
                if code and re.match(r"^\d{2}\.\d{2}", code):
                    out["table_b1_prohibited"].append({"category_code": code, "category_name": name})
            elif len(tds) == 1:
                cell = tds[0].get_text(strip=True)
                if "|" in cell and re.match(r"^\d{2}\.\d{2}", cell):
                    parts = cell.split("|", 1)
                    out["table_b1_prohibited"].append({
                        "category_code": (parts[0] or "").strip(),
                        "category_name": (parts[1] or "").strip(),
                    })
    return out


def parse_spices_table(html: str, table_id: str) -> List[Dict[str, Any]]:
    """解析香精香料表 B.2/B.3 页：Category, 中文名, 英文名, Code No., FEMA No., 表, Remarks"""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        header_like = tr.get_text()
        if "Category" in header_like and "Chinese Name" in header_like and "Code No." in header_like:
            continue
        cat = (tds[0].get_text(strip=True) or "").replace("\u200b", "")
        name_cn = (tds[1].get_text(strip=True) or "").replace("\u200b", "")
        name_en = (tds[2].get_text(strip=True) or "").replace("\u200b", "")
        code_no = (tds[3].get_text(strip=True) or "").replace("\u200b", "")
        fema = (tds[4].get_text(strip=True) or "").replace("\u200b", "") if len(tds) > 4 else ""
        cat_table = (tds[5].get_text(strip=True) or "").replace("\u200b", "") if len(tds) > 5 else ""
        remark = (tds[6].get_text(strip=True) or "").replace("\u200b", "") if len(tds) > 6 else ""
        if name_cn or name_en or code_no:
            rows.append({
                "category": cat,
                "name_cn": name_cn,
                "name_en": name_en,
                "code_no": code_no,
                "fema_no": fema,
                "category_table": cat_table,
                "remarks": remark or None,
            })
    return rows


def parse_homepage_rules(html: str) -> Dict[str, Any]:
    """解析首页：使用原则 1、2、3 等正文"""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    # 保留「Principles」「Table A.1」「Processing aids」等关键段落
    out = {"full_intro": text[:15000], "data_update_notice": ""}
    for p in soup.find_all("p"):
        t = p.get_text(strip=True)
        if "updated to Announcement" in t or "Data Update Notice" in t or "数据更新" in t:
            out["data_update_notice"] = t[:2000]
            break
    return out


def parse_appendix_d_functions(html: str) -> List[Dict[str, Any]]:
    """解析 func.html：附录D 食品添加剂功能类别定义（编号、功能、定义）"""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
        text = tr.get_text()
        if "Number" in text and "Function" in text and "Definition" in text:
            continue
        num = (tds[0].get_text(strip=True) or "").replace("\u200b", "")
        func_name = (tds[1].get_text(strip=True) or "").replace("\u200b", "")
        definition = (tds[2].get_text(strip=True) or "").replace("\u200b", "").replace("&quot;", '"')
        if num and re.match(r"^D\.\d+", num):
            rows.append({"number": num, "function": func_name, "definition": definition})
    return rows


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("开始爬取 2760.foodmate.net，输出目录: %s", OUT_DIR)

    # 1. 食品添加剂列表
    logger.info("1. 获取添加剂列表 addtives.html ...")
    html = get(f"{BASE_URL}/addtives.html")
    if not html:
        logger.error("无法获取添加剂列表")
        sys.exit(1)
    additives = parse_additive_list(html)
    logger.info("   解析到 %s 条添加剂", len(additives))
    with open(OUT_DIR / "additives.json", "w", encoding="utf-8") as f:
        json.dump(additives, f, ensure_ascii=False, indent=2)
    logger.info("   已保存 additives.json")

    # 2. 每个添加剂详情（使用范围）
    logger.info("2. 逐个获取添加剂详情（使用范围）...")
    full_additives = []
    for i, row in enumerate(additives):
        faid = row["id"]
        url = row["detail_url"]
        time.sleep(DELAY)
        detail_html = get(url)
        if detail_html:
            detail = parse_additive_detail(detail_html, faid)
            if not detail.get("name_cn") and row.get("name_cn"):
                detail["name_cn"] = row["name_cn"]
            if not detail.get("name_en") and row.get("name_en"):
                detail["name_en"] = row["name_en"]
            if not detail.get("cns"):
                detail["cns"] = row.get("cns", "")
            if not detail.get("ins"):
                detail["ins"] = row.get("ins", "")
            if not detail.get("function"):
                detail["function"] = row.get("function", "")
            full_additives.append(detail)
        else:
            full_additives.append({**row, "usage": []})
        if (i + 1) % 50 == 0:
            logger.info("   已处理 %s/%s", i + 1, len(additives))
    with open(OUT_DIR / "additives_with_usage.json", "w", encoding="utf-8") as f:
        json.dump(full_additives, f, ensure_ascii=False, indent=2)
    logger.info("   已保存 additives_with_usage.json（%s 条）", len(full_additives))

    # 3. 食品分类
    logger.info("3. 获取食品分类 category.html ...")
    time.sleep(DELAY)
    categories = []
    cat_html = get(f"{BASE_URL}/category.html")
    if cat_html:
        categories = parse_category_list(cat_html)
        logger.info("   解析到 %s 条食品分类", len(categories))
        with open(OUT_DIR / "categories.json", "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        logger.info("   已保存 categories.json")
    else:
        logger.warning("   未获取到 category.html")

    # 4. 加工助剂
    logger.info("4. 获取加工助剂 processing.html ...")
    time.sleep(DELAY)
    processing = []
    proc_html = get(f"{BASE_URL}/processing.html")
    if proc_html:
        processing = parse_processing_list(proc_html)
        logger.info("   解析到 %s 条加工助剂", len(processing))
        with open(OUT_DIR / "processing_aids.json", "w", encoding="utf-8") as f:
            json.dump(processing, f, ensure_ascii=False, indent=2)
        logger.info("   已保存 processing_aids.json")
    else:
        logger.warning("   未获取到 processing.html")

    # 5. 酶制剂
    logger.info("5. 获取酶制剂 enzyme.html ...")
    time.sleep(DELAY)
    enzymes = []
    enzyme_html = get(f"{BASE_URL}/enzyme.html")
    if enzyme_html:
        enzymes = parse_enzyme_list(enzyme_html)
        logger.info("   解析到 %s 条酶制剂", len(enzymes))
        with open(OUT_DIR / "enzymes.json", "w", encoding="utf-8") as f:
            json.dump(enzymes, f, ensure_ascii=False, indent=2)
        logger.info("   已保存 enzymes.json")
    else:
        logger.warning("   未获取到 enzyme.html")

    # 6. 香精香料：规则+表B.1、B.2、B.3
    logger.info("6. 获取香精香料 spices ...")
    time.sleep(DELAY)
    spices_rules = {}
    spices_b2 = []
    spices_b3 = []
    spices_html = get(f"{BASE_URL}/spices.html")
    if spices_html:
        spices_rules = parse_spices_page(spices_html)
        with open(OUT_DIR / "spices_rules.json", "w", encoding="utf-8") as f:
            json.dump(spices_rules, f, ensure_ascii=False, indent=2)
        logger.info("   已保存 spices_rules.json（原则 + 表B.1 禁止名单 %s 条）", len(spices_rules.get("table_b1_prohibited", [])))
    time.sleep(DELAY)
    b2_html = get(f"{BASE_URL}/spices/type/b2.html")
    if b2_html:
        spices_b2 = parse_spices_table(b2_html, "b2")
        with open(OUT_DIR / "spices_b2_natural.json", "w", encoding="utf-8") as f:
            json.dump(spices_b2, f, ensure_ascii=False, indent=2)
        logger.info("   已保存 spices_b2_natural.json（%s 条）", len(spices_b2))
    time.sleep(DELAY)
    b3_html = get(f"{BASE_URL}/spices/type/b3.html")
    if b3_html:
        spices_b3 = parse_spices_table(b3_html, "b3")
        with open(OUT_DIR / "spices_b3_synthetic.json", "w", encoding="utf-8") as f:
            json.dump(spices_b3, f, ensure_ascii=False, indent=2)
        logger.info("   已保存 spices_b3_synthetic.json（%s 条）", len(spices_b3))

    # 7. 首页使用原则
    logger.info("7. 获取首页使用原则 ...")
    time.sleep(DELAY)
    site_rules = {}
    index_html = get(BASE_URL + "/")
    if index_html:
        site_rules = parse_homepage_rules(index_html)
        with open(OUT_DIR / "site_rules.json", "w", encoding="utf-8") as f:
            json.dump(site_rules, f, ensure_ascii=False, indent=2)
        logger.info("   已保存 site_rules.json")

    # 8. 附录D 食品添加剂功能类别定义
    logger.info("8. 获取附录D 功能类别定义 func.html ...")
    time.sleep(DELAY)
    appendix_d = []
    func_html = get(f"{BASE_URL}/func.html")
    if func_html:
        appendix_d = parse_appendix_d_functions(func_html)
        logger.info("   解析到 %s 条功能类别", len(appendix_d))
        with open(OUT_DIR / "appendix_d_functions.json", "w", encoding="utf-8") as f:
            json.dump(appendix_d, f, ensure_ascii=False, indent=2)
        logger.info("   已保存 appendix_d_functions.json")
    else:
        logger.warning("   未获取到 func.html")

    index = {
        "source": BASE_URL,
        "additives_count": len(additives),
        "additives_with_usage_count": len(full_additives),
        "categories_count": len(categories),
        "processing_aids_count": len(processing),
        "enzymes_count": len(enzymes),
        "spices_b1_prohibited_count": len(spices_rules.get("table_b1_prohibited", [])),
        "spices_b2_natural_count": len(spices_b2),
        "spices_b3_synthetic_count": len(spices_b3),
        "appendix_d_functions_count": len(appendix_d),
        "files": [
            "additives.json",
            "additives_with_usage.json",
            "categories.json",
            "processing_aids.json",
            "enzymes.json",
            "spices_rules.json",
            "spices_b2_natural.json",
            "spices_b3_synthetic.json",
            "site_rules.json",
            "appendix_d_functions.json",
        ],
    }
    with open(OUT_DIR / "crawl_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    logger.info("完成。索引: crawl_index.json")


if __name__ == "__main__":
    main()
