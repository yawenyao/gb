"""
基础数据准备脚本
确保网站所需的基础数据都准备好
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extractors.pdf_extractor import PDFExtractor
from extractors.pdf_extractor_v2 import PDFExtractorV2
from extractors.pdf_extractor_ai import PDFExtractorAI
from processors.data_cleaner import DataCleaner
from processors.semantic_analyzer import SemanticAnalyzer
from processors.relationship_extractor import RelationshipExtractor
from processors.data_merger import DataMerger
from config import OUTPUT_DIR, PDF_PATH
from utils.logger import logger

# Neo4j导入器（可选）
try:
    from importers.graph_importer import GraphImporter
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j模块未安装，将跳过Neo4j导入功能")


def prepare_base_data():
    """准备基础数据"""
    logger.info("=" * 80)
    logger.info("GB 2760-2024 基础数据准备")
    logger.info("=" * 80)
    
    # 初始化组件
    # 选择提取器：AI增强版 > V2优化版 > 原版
    use_ai = os.environ.get('USE_AI_EXTRACTION', 'false').lower() == 'true'
    
    if use_ai:
        logger.info("使用AI增强提取器")
        pdf_extractor_ai = PDFExtractorAI(PDF_PATH)
    pdf_extractor_v2 = PDFExtractorV2(PDF_PATH)
    pdf_extractor = PDFExtractor(PDF_PATH)  # 保留原版作为备用
    
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
        'mixing_relationships': [],
        'statistics': {}
    }
    
    # ========== 步骤1: 提取PDF数据 ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤1: 提取PDF数据")
    logger.info("=" * 80)
    
    try:
        # 提取表A.1（优先使用AI增强版）
        logger.info("\n[1.1] 提取表A.1（食品添加剂使用规定）...")
        table_a1_raw = []
        
        if use_ai:
            try:
                logger.info("使用AI增强提取器...")
                records, validation_report = pdf_extractor_ai.extract_with_ai_validation("A.1", validate=True)
                table_a1_raw = records
                logger.info(f"✓ AI增强提取器提取了{len(table_a1_raw)}条记录")
                logger.info(f"  有效记录: {validation_report.get('valid_records', 0)}")
                logger.info(f"  无效记录: {validation_report.get('invalid_records', 0)}")
            except Exception as e:
                logger.warning(f"AI提取器失败，使用V2版: {e}")
                use_ai = False
        
        if not use_ai:
            try:
                table_a1_raw = pdf_extractor_v2.extract_table_a1()
                logger.info(f"✓ V2提取器提取了{len(table_a1_raw)}条原始记录")
            except Exception as e:
                logger.warning(f"V2提取器失败，使用原版: {e}")
                table_a1_raw = pdf_extractor.extract_tables("A.1")
                logger.info(f"✓ 原版提取器提取了{len(table_a1_raw)}条原始记录")
        
        # 清洗表A.1
        table_a1_cleaned = []
        for row in table_a1_raw:
            cleaned = data_cleaner.clean_additive_data(row)
            table_a1_cleaned.append(cleaned)
        logger.info(f"✓ 清洗后{len(table_a1_cleaned)}条记录")
        
        # 提取表A.2
        logger.info("\n[1.2] 提取表A.2...")
        table_a2_raw = pdf_extractor.extract_tables("A.2")
        table_a2_cleaned = []
        for row in table_a2_raw:
            cleaned = row.copy()
            cleaned['source'] = 'PDF'
            table_a2_cleaned.append(cleaned)
        logger.info(f"✓ 提取了{len(table_a2_cleaned)}条记录")
        
        # 提取表E.1
        logger.info("\n[1.3] 提取表E.1...")
        table_e1_raw = pdf_extractor.extract_tables("E.1")
        table_e1_cleaned = []
        for row in table_e1_raw:
            cleaned = data_cleaner.clean_food_category_data(row)
            table_e1_cleaned.append(cleaned)
        logger.info(f"✓ 提取了{len(table_e1_cleaned)}条记录")
        
    except Exception as e:
        logger.error(f"PDF提取失败: {e}", exc_info=True)
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
        
        # 提取层级关系
        logger.info("\n[2.2] 提取层级关系...")
        hierarchy_relationships = relationship_extractor.extract_category_hierarchy(table_e1_cleaned)
        all_data['hierarchy_relationships'] = hierarchy_relationships
        logger.info(f"✓ 提取了{len(hierarchy_relationships)}个层级关系")
        
        # 提取功能关系
        logger.info("\n[2.3] 提取功能关系...")
        function_relationships = relationship_extractor.extract_function_relationships(table_a1_cleaned)
        all_data['function_relationships'] = function_relationships
        logger.info(f"✓ 提取了{len(function_relationships)}个功能关系")
        
        # 提取排除关系
        logger.info("\n[2.4] 提取排除关系...")
        exclusion_relationships = relationship_extractor.extract_exclusion_relationships(
            table_a2_cleaned, usage_relationships
        )
        all_data['exclusion_relationships'] = exclusion_relationships
        logger.info(f"✓ 提取了{len(exclusion_relationships)}个排除关系")
        
        # 提取混合使用关系
        logger.info("\n[2.5] 提取混合使用关系...")
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
                # 获取功能
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
                    'version': 'GB2760-2024'
                }
        all_data['additives'] = list(additives_dict.values())
        logger.info(f"✓ 准备了{len(all_data['additives'])}个添加剂节点")
        
        # 准备食品类别节点
        logger.info("\n[3.2] 准备食品类别节点...")
        for row in table_e1_cleaned:
            code = row.get('category_code') or row.get('food_category_code')
            if code:
                all_data['food_categories'].append({
                    'id': code,
                    'code': code,
                    'name': row.get('category_name') or row.get('food_name'),
                    'level': row.get('level', data_cleaner._extract_level(code)),
                    'parent_code': row.get('parent_code') or data_cleaner._extract_parent_code(code),
                    'description': row.get('description'),
                    'source': 'PDF'
                })
        logger.info(f"✓ 准备了{len(all_data['food_categories'])}个食品类别节点")
        
    except Exception as e:
        logger.error(f"节点数据准备失败: {e}", exc_info=True)
        return False
    
    # ========== 步骤4: 计算统计信息 ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤4: 计算统计信息")
    logger.info("=" * 80)
    
    all_data['statistics'] = {
        'additives_count': len(all_data['additives']),
        'food_categories_count': len(all_data['food_categories']),
        'usage_relationships_count': len(all_data['usage_relationships']),
        'function_relationships_count': len(all_data['function_relationships']),
        'hierarchy_relationships_count': len(all_data['hierarchy_relationships']),
        'exclusion_relationships_count': len(all_data['exclusion_relationships']),
        'mixing_relationships_count': len(all_data['mixing_relationships']),
    }
    
    logger.info("\n数据统计:")
    for key, value in all_data['statistics'].items():
        logger.info(f"  {key}: {value}")
    
    # ========== 步骤5: 保存数据 ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤5: 保存数据")
    logger.info("=" * 80)
    
    try:
        # 保存完整数据
        base_data_file = OUTPUT_DIR / 'base_data.json'
        with open(base_data_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 基础数据已保存至: {base_data_file}")
        
        # 保存图数据库格式数据
        graph_data = {
            'additives': all_data['additives'],
            'food_categories': all_data['food_categories'],
            'usage_relationships': [
                {
                    'additive_id': r['additive_name'],
                    'food_code': r['food_category_code'],
                    'max_usage': r.get('max_usage'),
                    'unit': r.get('unit'),
                    'residue_limit': r.get('residue_limit'),
                    'note': r.get('note'),
                    'exception': r.get('exception', False),
                    'source': r.get('source', 'PDF')
                }
                for r in all_data['usage_relationships']
            ],
            'function_relationships': all_data['function_relationships'],
            'exclusion_relationships': all_data['exclusion_relationships'],
            'mixing_relationships': all_data['mixing_relationships'],
        }
        
        graph_data_file = OUTPUT_DIR / 'graph_data_final.json'
        with open(graph_data_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 图数据库数据已保存至: {graph_data_file}")
        
        # 保存统计报告
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'statistics': all_data['statistics'],
            'files': {
                'base_data': str(base_data_file),
                'graph_data': str(graph_data_file)
            }
        }
        
        report_file = OUTPUT_DIR / 'data_preparation_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 准备报告已保存至: {report_file}")
        
    except Exception as e:
        logger.error(f"数据保存失败: {e}", exc_info=True)
        return False
    
    # ========== 步骤6: 可选导入Neo4j ==========
    logger.info("\n" + "=" * 80)
    logger.info("步骤6: 可选导入Neo4j")
    logger.info("=" * 80)
    
    if not NEO4J_AVAILABLE:
        logger.info("\n⚠️ Neo4j模块未安装，跳过Neo4j导入")
        logger.info("如需导入Neo4j，请安装: pip install neo4j")
        import_neo4j = 'n'
    else:
        import_neo4j = input("\n是否导入Neo4j数据库？(y/n，默认n): ").strip().lower()
    
    if import_neo4j == 'y' and NEO4J_AVAILABLE:
        try:
            logger.info("\n连接Neo4j数据库...")
            importer = GraphImporter()
            
            logger.info("导入节点和关系...")
            importer.import_additives(all_data['additives'])
            importer.import_food_categories(all_data['food_categories'])
            importer.import_usage_relationships([
                {
                    'additive_name': r['additive_name'],
                    'food_category_code': r['food_category_code'],
                    'max_usage': r.get('max_usage'),
                    'unit': r.get('unit'),
                    'residue_limit': r.get('residue_limit'),
                    'note': r.get('note'),
                    'exception': r.get('exception', False),
                    'source': r.get('source', 'PDF')
                }
                for r in all_data['usage_relationships']
            ])
            importer.import_function_relationships(all_data['function_relationships'])
            importer.import_exclusion_relationships(all_data['exclusion_relationships'])
            importer.import_mixing_relationships(all_data['mixing_relationships'])
            
            logger.info("获取统计信息...")
            stats = importer.get_statistics()
            logger.info("\nNeo4j数据库统计信息:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
            
            importer.close()
            logger.info("\n✓ 数据导入Neo4j完成！")
            
        except Exception as e:
            logger.error(f"导入Neo4j失败: {e}", exc_info=True)
            logger.info("请检查Neo4j是否启动，以及连接配置是否正确")
    
    # ========== 完成 ==========
    logger.info("\n" + "=" * 80)
    logger.info("基础数据准备完成！")
    logger.info("=" * 80)
    
    logger.info("\n输出文件:")
    logger.info(f"  1. 基础数据: {OUTPUT_DIR / 'base_data.json'}")
    logger.info(f"  2. 图数据库数据: {OUTPUT_DIR / 'graph_data_final.json'}")
    logger.info(f"  3. 准备报告: {OUTPUT_DIR / 'data_preparation_report.json'}")
    
    return True


if __name__ == '__main__':
    success = prepare_base_data()
    sys.exit(0 if success else 1)
