"""
PDF提取器测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.pdf_extractor import PDFExtractor
from utils.logger import logger
from config import PDF_PATH


def test_pdf_extraction():
    """测试PDF提取"""
    logger.info("开始测试PDF提取器")
    
    try:
        extractor = PDFExtractor(PDF_PATH)
        
        # 测试提取表A.1
        logger.info("\n测试提取表A.1...")
        table_a1 = extractor.extract_tables("A.1")
        logger.info(f"提取了{len(table_a1)}条记录")
        
        if table_a1:
            logger.info("\n前3条记录示例:")
            for i, row in enumerate(table_a1[:3], 1):
                logger.info(f"\n记录 {i}:")
                for key, value in row.items():
                    logger.info(f"  {key}: {value}")
        
        # 测试提取表A.2
        logger.info("\n测试提取表A.2...")
        table_a2 = extractor.extract_tables("A.2")
        logger.info(f"提取了{len(table_a2)}条记录")
        
        # 测试提取表E.1
        logger.info("\n测试提取表E.1...")
        table_e1 = extractor.extract_tables("E.1")
        logger.info(f"提取了{len(table_e1)}条记录")
        
        logger.info("\n✓ PDF提取测试完成")
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)


if __name__ == '__main__':
    test_pdf_extraction()
