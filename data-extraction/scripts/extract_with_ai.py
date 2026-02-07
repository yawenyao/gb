"""
使用AI增强提取PDF数据
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.pdf_extractor_ai import PDFExtractorAI
from config import PDF_PATH, OUTPUT_DIR
from utils.logger import logger


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("AI增强PDF数据提取")
    logger.info("=" * 80)
    
    # 初始化AI提取器
    extractor = PDFExtractorAI(PDF_PATH)
    
    # 提取表A.1
    logger.info("\n开始提取表A.1（使用AI增强）...")
    records, validation_report = extractor.extract_with_ai_validation(
        table_name="A.1",
        validate=True
    )
    
    logger.info(f"\n提取完成！")
    logger.info(f"总记录数: {validation_report['total_records']}")
    logger.info(f"有效记录数: {validation_report['valid_records']}")
    logger.info(f"无效记录数: {validation_report['invalid_records']}")
    
    if validation_report['errors']:
        logger.warning(f"\n发现{len(validation_report['errors'])}个错误:")
        for error in validation_report['errors'][:5]:
            logger.warning(f"  - {error}")
    
    if validation_report['warnings']:
        logger.warning(f"\n发现{len(validation_report['warnings'])}个警告:")
        for warning in validation_report['warnings'][:5]:
            logger.warning(f"  - {warning}")
    
    # 保存数据
    output_file = OUTPUT_DIR / 'pdf_data_ai_enhanced.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'records': records,
            'validation_report': validation_report,
            'metadata': {
                'table_name': 'A.1',
                'total_records': len(records),
                'ai_enhanced': True
            }
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n数据已保存至: {output_file}")
    
    # 显示示例数据
    if records:
        logger.info("\n前3条记录示例:")
        for i, record in enumerate(records[:3], 1):
            logger.info(f"\n记录{i}:")
            logger.info(f"  添加剂: {record.get('additive_name')}")
            logger.info(f"  CNS: {record.get('cns')}")
            logger.info(f"  食品分类号: {record.get('food_category_code')}")
            logger.info(f"  食品名称: {record.get('food_name')}")
            logger.info(f"  最大使用量: {record.get('max_usage')}")


if __name__ == '__main__':
    main()
