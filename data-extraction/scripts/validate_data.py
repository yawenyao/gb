"""
数据验证脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators.data_validator import DataValidator
from config import OUTPUT_DIR
from utils.logger import logger


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("数据验证工具")
    logger.info("=" * 60)
    
    validator = DataValidator()
    results = []
    
    # 验证清洗后的数据
    cleaned_file = OUTPUT_DIR / 'pdf_data_cleaned.json'
    if cleaned_file.exists():
        logger.info(f"\n验证文件: {cleaned_file}")
        result = validator.validate_file(cleaned_file)
        results.append(result)
        
        if result['valid']:
            logger.info("✓ 文件验证通过")
        else:
            logger.warning("✗ 文件验证失败")
            for error in result['errors']:
                logger.error(f"  错误: {error}")
        
        for warning in result['warnings']:
            logger.warning(f"  警告: {warning}")
    else:
        logger.warning(f"文件不存在: {cleaned_file}")
    
    # 验证关系数据
    relationships_file = OUTPUT_DIR / 'relationships.json'
    if relationships_file.exists():
        logger.info(f"\n验证文件: {relationships_file}")
        result = validator.validate_file(relationships_file)
        results.append(result)
        
        if result['valid']:
            logger.info("✓ 文件验证通过")
        else:
            logger.warning("✗ 文件验证失败")
    else:
        logger.warning(f"文件不存在: {relationships_file}")
    
    # 生成验证报告
    if results:
        report_file = OUTPUT_DIR / 'validation_report.json'
        validator.generate_validation_report(results, report_file)
        logger.info(f"\n验证报告已保存至: {report_file}")


if __name__ == '__main__':
    main()
