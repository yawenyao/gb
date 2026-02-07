"""
测试AI增强的PDF提取
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.pdf_extractor_ai import PDFExtractorAI
from config import PDF_PATH
from utils.logger import logger


def test_ai_extraction():
    """测试AI提取功能"""
    logger.info("=" * 60)
    logger.info("测试AI增强的PDF提取")
    logger.info("=" * 60)
    
    # 创建AI提取器
    extractor = PDFExtractorAI(PDF_PATH, use_ai=True)
    
    # 测试提取少量数据（前几页）
    logger.info("\n测试提取前3页数据...")
    
    try:
        import pdfplumber
        with pdfplumber.open(PDF_PATH) as pdf:
            # 提取第8-10页（表A.1开始的地方）
            pages_data = []
            for page_num in range(8, 11):
                if page_num > len(pdf.pages):
                    break
                page = pdf.pages[page_num - 1]
                text = page.extract_text()
                tables = page.extract_tables()
                pages_data.append({
                    'page_num': page_num,
                    'text': text or '',
                    'tables': tables or []
                })
            
            # 使用AI提取
            records = extractor._ai_extract_table_a1(pages_data)
            
            logger.info(f"\n✓ AI提取了{len(records)}条记录")
            
            if records:
                logger.info("\n前3条记录示例：")
                import json
                for i, record in enumerate(records[:3], 1):
                    print(f"\n记录{i}:")
                    print(json.dumps(record, indent=2, ensure_ascii=False))
            
            # 测试验证功能
            if records:
                logger.info("\n测试AI验证功能...")
                validated = extractor.extract_with_ai_validation(records[:5])  # 只验证5条
                logger.info(f"✓ 验证了{len(validated)}条记录")
    
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)


if __name__ == '__main__':
    test_ai_extraction()
