"""
检查提取的数据结构
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.pdf_extractor import PDFExtractor
from config import PDF_PATH, OUTPUT_DIR
from utils.logger import logger


def inspect_data():
    """检查提取的数据"""
    logger.info("检查提取的数据结构...")
    
    extractor = PDFExtractor(PDF_PATH)
    
    # 提取少量数据用于检查
    logger.info("提取表A.1的前几页...")
    table_a1_sample = []
    
    try:
        import pdfplumber
        with pdfplumber.open(PDF_PATH) as pdf:
            for page_num in range(8, 12):  # 只检查前几页
                if page_num >= len(pdf.pages):
                    break
                page = pdf.pages[page_num]
                text = page.extract_text()
                
                if extractor._is_target_table(text, "A.1"):
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            processed = extractor._process_table(table, "A.1", page_num)
                            table_a1_sample.extend(processed[:5])  # 每页只取前5条
                            break
    
    except Exception as e:
        logger.error(f"提取失败: {e}", exc_info=True)
        return
    
    logger.info(f"提取了{len(table_a1_sample)}条样本记录")
    
    if table_a1_sample:
        logger.info("\n第一条记录:")
        print(json.dumps(table_a1_sample[0], indent=2, ensure_ascii=False))
        
        logger.info("\n所有字段:")
        all_keys = set()
        for record in table_a1_sample:
            all_keys.update(record.keys())
        print(sorted(all_keys))
        
        # 保存样本数据
        sample_file = OUTPUT_DIR / 'sample_data.json'
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(table_a1_sample, f, ensure_ascii=False, indent=2)
        logger.info(f"\n样本数据已保存至: {sample_file}")
    else:
        logger.warning("未提取到数据，可能需要调整提取逻辑")


if __name__ == '__main__':
    inspect_data()
