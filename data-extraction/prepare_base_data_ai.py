"""
AI增强的基础数据准备脚本
使用AI理解PDF语义，提取完整且正确的数据
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extractors.pdf_extractor_ai import PDFExtractorAI
from extractors.pdf_extractor_v2 import PDFExtractorV2  # 作为回退方案
from processors.data_cleaner import DataCleaner
from processors.relationship_extractor import RelationshipExtractor
from processors.data_merger import DataMerger
from config import OUTPUT_DIR, PDF_PATH
from utils.logger import logger


def prepare_base_data_with_ai(use_ai: bool = True):
    """
    使用AI准备基础数据
    
    Args:
        use_ai: 是否使用AI提取（默认True）
    """
    logger.info("=" * 80)
    logger.info("GB 2760-2024 基础数据准备（AI增强版）")
    logger.info("=" * 80)
    
    # 初始化组件
    if use_ai:
        pdf_extractor = PDFExtractorAI(PDF_PATH, use_ai=True)
        logger.info("✓ 使用AI增强提取器")
    else:
        pdf_extractor = PDFExtractorV2(PDF_PATH)
        logger.info("✓ 使用传统提取器")
    
    data_cleaner = DataCleaner()
    relationship_extractor = RelationshipExtractor()
    data_merger = DataMerger()
    
    all_data = {
        'additives': [],
        'food_categories': [],
        'usage_relationships': [],
        'function_relationships': [],
        'hierarchy_relationships': [],
        'exclusion_relationships': [],
        'mixing_relationships': []
    }
    
    # ========== 步骤1: 提取PDF数据 ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤1: 提取PDF数据（AI增强）")
    logger.info("=" * 80)
    
    try:
        # 提取表A.1（使用AI）
        logger.info("\n[1.1] 使用AI提取表A.1...")
        if use_ai:
            table_a1_raw = pdf_extractor.extract_table_a1_with_ai()
        else:
            table_a1_raw = pdf_extractor.extract_table_a1()
        
        logger.info(f"✓ 提取了{len(table_a1_raw)}条原始记录")
        
        # AI验证和补全数据
        if use_ai:
            logger.info("\n[1.2] 使用AI验证和补全数据...")
            table_a1_raw = pdf_extractor.extract_with_ai_validation(table_a1_raw)
            logger.info(f"✓ AI验证完成，共{len(table_a1_raw)}条记录")
        
        # 清洗数据
        logger.info("\n[1.3] 清洗数据...")
        table_a1_cleaned = []
        for row in table_a1_raw:
            cleaned = data_cleaner.clean_additive_data(row)
            table_a1_cleaned.append(cleaned)
        logger.info(f"✓ 清洗后{len(table_a1_cleaned)}条记录")
        
        # 提取表A.2（暂时使用传统方法）
        logger.info("\n[1.4] 提取表A.2...")
        from extractors.pdf_extractor import PDFExtractor
        pdf_extractor_traditional = PDFExtractor(PDF_PATH)
        table_a2_raw = pdf_extractor_traditional.extract_tables("A.2")
        table_a2_cleaned = [data_cleaner.clean_additive_data(row) for row in table_a2_raw]
        logger.info(f"✓ 提取了{len(table_a2_cleaned)}条记录")
        
    except Exception as e:
        logger.error(f"数据提取失败: {e}", exc_info=True)
        return False
    
    # ========== 步骤2: 提取关系 ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤2: 提取关系")
    logger.info("=" * 80)
    
    try:
        # 提取使用关系
        logger.info("\n[2.1] 提取使用关系...")
        usage_relationships = relationship_extractor.extract_usage_relationships(table_a1_cleaned)
        all_data['usage_relationships'] = usage_relationships
        logger.info(f"✓ 提取了{len(usage_relationships)}个使用关系")
        
        # 提取功能关系
        logger.info("\n[2.2] 提取功能关系...")
        function_relationships = relationship_extractor.extract_function_relationships(table_a1_cleaned)
        all_data['function_relationships'] = function_relationships
        logger.info(f"✓ 提取了{len(function_relationships)}个功能关系")
        
        # 提取混合使用关系
        logger.info("\n[2.3] 提取混合使用关系...")
        mixing_relationships = relationship_extractor.extract_mixing_relationships(table_a1_cleaned)
        all_data['mixing_relationships'] = mixing_relationships
        logger.info(f"✓ 提取了{len(mixing_relationships)}个混合使用关系")
        
    except Exception as e:
        logger.error(f"关系提取失败: {e}", exc_info=True)
        return False
    
    # ========== 步骤3: 准备节点数据 ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤3: 准备节点数据")
    logger.info("=" * 80)
    
    try:
        # 准备添加剂节点
        logger.info("\n[3.1] 准备添加剂节点...")
        additives_dict = {}
        for row in table_a1_cleaned:
            name = row.get('additive_name')
            if not name or name in ['食品添加剂的允许使用品种', '允许使用品种', '—']:
                continue
            
            if name not in additives_dict:
                func = row.get('function')
                if isinstance(func, str):
                    functions = [func] if func else []
                elif isinstance(func, list):
                    functions = func
                else:
                    functions = []
                
                additives_dict[name] = {
                    'id': name,
                    'name': name,
                    'cns': row.get('cns'),
                    'ins': row.get('ins'),
                    'function': functions,
                    'source': 'PDF',
                    'extracted_by': 'AI' if use_ai else 'Traditional',
                    'version': 'GB2760-2024'
                }
        
        all_data['additives'] = list(additives_dict.values())
        logger.info(f"✓ 准备了{len(all_data['additives'])}个添加剂节点")
        
    except Exception as e:
        logger.error(f"节点数据准备失败: {e}", exc_info=True)
        return False
    
    # ========== 步骤4: 计算统计信息 ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤4: 计算统计信息")
    logger.info("=" * 80)
    
    statistics = {
        'additives_count': len(all_data['additives']),
        'food_categories_count': len(all_data['food_categories']),
        'usage_relationships_count': len(all_data['usage_relationships']),
        'function_relationships_count': len(all_data['function_relationships']),
        'hierarchy_relationships_count': len(all_data['hierarchy_relationships']),
        'exclusion_relationships_count': len(all_data['exclusion_relationships']),
        'mixing_relationships_count': len(all_data['mixing_relationships']),
        'extraction_method': 'AI' if use_ai else 'Traditional'
    }
    
    all_data['statistics'] = statistics
    
    logger.info("\n数据统计:")
    for key, value in statistics.items():
        logger.info(f"  {key}: {value}")
    
    # ========== 步骤5: 保存数据 ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤5: 保存数据")
    logger.info("=" * 80)
    
    try:
        # 保存基础数据
        base_data_file = OUTPUT_DIR / 'base_data_ai.json' if use_ai else OUTPUT_DIR / 'base_data.json'
        with open(base_data_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 基础数据已保存至: {base_data_file}")
        
        # 保存报告
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'statistics': statistics,
            'files': {
                'base_data': str(base_data_file)
            },
            'extraction_method': 'AI' if use_ai else 'Traditional'
        }
        
        report_file = OUTPUT_DIR / 'data_preparation_report_ai.json' if use_ai else OUTPUT_DIR / 'data_preparation_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 准备报告已保存至: {report_file}")
        
    except Exception as e:
        logger.error(f"保存数据失败: {e}", exc_info=True)
        return False
    
    logger.info("\n" + "=" * 80)
    logger.info("基础数据准备完成！")
    logger.info("=" * 80)
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='使用AI准备基础数据')
    parser.add_argument('--no-ai', action='store_true', help='不使用AI，使用传统方法')
    args = parser.parse_args()
    
    use_ai = not args.no_ai
    
    if use_ai:
        logger.info("使用AI增强提取模式")
    else:
        logger.info("使用传统提取模式")
    
    success = prepare_base_data_with_ai(use_ai=use_ai)
    
    if success:
        logger.info("\n✅ 数据准备成功！")
    else:
        logger.error("\n❌ 数据准备失败！")
        sys.exit(1)
