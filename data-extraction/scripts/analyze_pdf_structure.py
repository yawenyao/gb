"""
分析PDF表格结构
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pdfplumber
from config import PDF_PATH
from utils.logger import logger


def analyze_structure():
    """分析PDF表格结构"""
    logger.info("分析PDF表格结构...")
    
    with pdfplumber.open(PDF_PATH) as pdf:
        # 检查第8页（表A.1开始的地方）
        page = pdf.pages[7]  # 0-based index
        text = page.extract_text()
        
        logger.info("\n第8页文本片段（前500字符）:")
        print(text[:500])
        
        logger.info("\n提取表格:")
        tables = page.extract_tables()
        logger.info(f"找到{len(tables)}个表格")
        
        if tables:
            table = tables[0]
            logger.info(f"\n表格尺寸: {len(table)}行 x {len(table[0]) if table else 0}列")
            
            logger.info("\n前5行:")
            for i, row in enumerate(table[:5]):
                logger.info(f"\n第{i+1}行 ({len(row)}列):")
                for j, cell in enumerate(row):
                    if cell:
                        print(f"  列{j}: {repr(cell)}")


if __name__ == '__main__':
    analyze_structure()
