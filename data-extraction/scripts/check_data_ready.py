"""
检查数据是否准备完成
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OUTPUT_DIR
from utils.logger import logger


def check_data_ready():
    """检查数据是否准备完成"""
    logger.info("=" * 60)
    logger.info("检查数据准备状态")
    logger.info("=" * 60)
    
    required_files = [
        'base_data.json',
        'graph_data_final.json',
        'data_preparation_report.json'
    ]
    
    all_ready = True
    
    for filename in required_files:
        file_path = OUTPUT_DIR / filename
        if file_path.exists():
            logger.info(f"✓ {filename} 存在")
            
            # 检查文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if filename == 'base_data.json':
                    stats = data.get('statistics', {})
                    logger.info(f"  数据统计:")
                    for key, value in stats.items():
                        logger.info(f"    {key}: {value}")
                
            except Exception as e:
                logger.warning(f"  ⚠️ 文件读取失败: {e}")
                all_ready = False
        else:
            logger.warning(f"✗ {filename} 不存在")
            all_ready = False
    
    if all_ready:
        logger.info("\n" + "=" * 60)
        logger.info("✓ 所有基础数据已准备完成！")
        logger.info("=" * 60)
        logger.info("\n可以使用以下数据文件:")
        logger.info(f"  1. {OUTPUT_DIR / 'base_data.json'}")
        logger.info(f"  2. {OUTPUT_DIR / 'graph_data_final.json'}")
        logger.info(f"  3. {OUTPUT_DIR / 'data_preparation_report.json'}")
        return True
    else:
        logger.info("\n" + "=" * 60)
        logger.info("✗ 数据尚未准备完成")
        logger.info("=" * 60)
        logger.info("\n请运行以下命令准备数据:")
        logger.info("  python prepare_base_data.py")
        return False


if __name__ == '__main__':
    success = check_data_ready()
    sys.exit(0 if success else 1)
