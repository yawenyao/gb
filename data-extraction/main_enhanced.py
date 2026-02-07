"""
增强版主程序 - 完整的数据提取和处理流程
"""
import json
from pathlib import Path
from extractors.pdf_extractor import PDFExtractor
from extractors.web_crawler import WebCrawler
from processors.data_cleaner import DataCleaner
from processors.semantic_analyzer import SemanticAnalyzer
from processors.relationship_extractor import RelationshipExtractor
from importers.graph_importer import GraphImporter
from config import OUTPUT_DIR
from utils.logger import logger


def main():
    """主函数 - 完整的数据提取和处理流程"""
    logger.info("=" * 60)
    logger.info("GB 2760-2024 数据提取和处理工具 - 增强版")
    logger.info("=" * 60)
    
    # 初始化组件
    pdf_extractor = PDFExtractor()
    data_cleaner = DataCleaner()
    semantic_analyzer = SemanticAnalyzer()
    relationship_extractor = RelationshipExtractor()
    
    # ========== Phase 1: PDF数据提取 ==========
    logger.info("\n" + "=" * 60)
    logger.info("Phase 1: PDF数据提取")
    logger.info("=" * 60)
    
    pdf_data = {}
    
    try:
        # 提取表A.1
        logger.info("\n[1.1] 提取表A.1（食品添加剂使用规定）...")
        table_a1_raw = pdf_extractor.extract_tables("A.1")
        pdf_data['table_a1_raw'] = table_a1_raw
        logger.info(f"✓ 表A.1提取完成，共{len(table_a1_raw)}条记录")
        
        # 提取表A.2
        logger.info("\n[1.2] 提取表A.2（例外食品编号）...")
        table_a2_raw = pdf_extractor.extract_tables("A.2")
        pdf_data['table_a2_raw'] = table_a2_raw
        logger.info(f"✓ 表A.2提取完成，共{len(table_a2_raw)}条记录")
        
        # 提取表E.1
        logger.info("\n[1.3] 提取表E.1（食品分类系统）...")
        table_e1_raw = pdf_extractor.extract_tables("E.1")
        pdf_data['table_e1_raw'] = table_e1_raw
        logger.info(f"✓ 表E.1提取完成，共{len(table_e1_raw)}条记录")
        
    except Exception as e:
        logger.error(f"PDF提取失败: {e}", exc_info=True)
        return
    
    # 保存原始数据
    raw_output_file = OUTPUT_DIR / 'pdf_data_raw.json'
    with open(raw_output_file, 'w', encoding='utf-8') as f:
        json.dump(pdf_data, f, ensure_ascii=False, indent=2)
    logger.info(f"\n✓ 原始数据已保存至: {raw_output_file}")
    
    # ========== Phase 2: 数据清洗 ==========
    logger.info("\n" + "=" * 60)
    logger.info("Phase 2: 数据清洗和标准化")
    logger.info("=" * 60)
    
    cleaned_data = {}
    
    try:
        # 清洗表A.1
        logger.info("\n[2.1] 清洗表A.1数据...")
        table_a1_cleaned = []
        for row in table_a1_raw:
            cleaned_row = data_cleaner.clean_additive_data(row)
            table_a1_cleaned.append(cleaned_row)
        cleaned_data['table_a1'] = table_a1_cleaned
        logger.info(f"✓ 表A.1清洗完成，共{len(table_a1_cleaned)}条记录")
        
        # 清洗表A.2
        logger.info("\n[2.2] 清洗表A.2数据...")
        table_a2_cleaned = []
        for row in table_a2_raw:
            cleaned_row = row.copy()  # A.2数据较简单，直接复制
            cleaned_row['source'] = 'PDF'
            table_a2_cleaned.append(cleaned_row)
        cleaned_data['table_a2'] = table_a2_cleaned
        logger.info(f"✓ 表A.2清洗完成，共{len(table_a2_cleaned)}条记录")
        
        # 清洗表E.1
        logger.info("\n[2.3] 清洗表E.1数据...")
        table_e1_cleaned = []
        for row in table_e1_raw:
            cleaned_row = data_cleaner.clean_food_category_data(row)
            table_e1_cleaned.append(cleaned_row)
        cleaned_data['table_e1'] = table_e1_cleaned
        logger.info(f"✓ 表E.1清洗完成，共{len(table_e1_cleaned)}条记录")
        
    except Exception as e:
        logger.error(f"数据清洗失败: {e}", exc_info=True)
        return
    
    # 保存清洗后的数据
    cleaned_output_file = OUTPUT_DIR / 'pdf_data_cleaned.json'
    with open(cleaned_output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    logger.info(f"\n✓ 清洗后数据已保存至: {cleaned_output_file}")
    
    # ========== Phase 3: 关系提取 ==========
    logger.info("\n" + "=" * 60)
    logger.info("Phase 3: 关系提取")
    logger.info("=" * 60)
    
    relationships = {}
    
    try:
        # 提取使用关系
        logger.info("\n[3.1] 提取使用关系...")
        usage_relationships = relationship_extractor.extract_usage_relationships(table_a1_cleaned)
        relationships['usage_relationships'] = usage_relationships
        logger.info(f"✓ 提取了{len(usage_relationships)}个使用关系")
        
        # 提取层级关系
        logger.info("\n[3.2] 提取食品类别层级关系...")
        hierarchy_relationships = relationship_extractor.extract_category_hierarchy(table_e1_cleaned)
        relationships['hierarchy_relationships'] = hierarchy_relationships
        logger.info(f"✓ 提取了{len(hierarchy_relationships)}个层级关系")
        
        # 提取功能关系
        logger.info("\n[3.3] 提取功能关系...")
        function_relationships = relationship_extractor.extract_function_relationships(table_a1_cleaned)
        relationships['function_relationships'] = function_relationships
        logger.info(f"✓ 提取了{len(function_relationships)}个功能关系")
        
        # 提取排除关系
        logger.info("\n[3.4] 提取排除关系...")
        exclusion_relationships = relationship_extractor.extract_exclusion_relationships(
            table_a2_cleaned, usage_relationships
        )
        relationships['exclusion_relationships'] = exclusion_relationships
        logger.info(f"✓ 提取了{len(exclusion_relationships)}个排除关系")
        
        # 提取混合使用关系
        logger.info("\n[3.5] 提取混合使用关系...")
        mixing_relationships = relationship_extractor.extract_mixing_relationships(table_a1_cleaned)
        relationships['mixing_relationships'] = mixing_relationships
        logger.info(f"✓ 提取了{len(mixing_relationships)}个混合使用关系")
        
    except Exception as e:
        logger.error(f"关系提取失败: {e}", exc_info=True)
        return
    
    # 保存关系数据
    relationships_output_file = OUTPUT_DIR / 'relationships.json'
    with open(relationships_output_file, 'w', encoding='utf-8') as f:
        json.dump(relationships, f, ensure_ascii=False, indent=2)
    logger.info(f"\n✓ 关系数据已保存至: {relationships_output_file}")
    
    # ========== Phase 4: 准备图数据库数据 ==========
    logger.info("\n" + "=" * 60)
    logger.info("Phase 4: 准备图数据库数据")
    logger.info("=" * 60)
    
    graph_data = {}
    
    try:
        # 准备添加剂节点
        logger.info("\n[4.1] 准备添加剂节点...")
        additives = {}
        for row in table_a1_cleaned:
            additive_name = row.get('additive_name')
            if additive_name and additive_name not in additives:
                additives[additive_name] = {
                    'id': additive_name,
                    'name': additive_name,
                    'function': row.get('function', []),
                    'source': 'PDF',
                    'version': 'GB2760-2024'
                }
        graph_data['additives'] = list(additives.values())
        logger.info(f"✓ 准备了{len(graph_data['additives'])}个添加剂节点")
        
        # 准备食品类别节点
        logger.info("\n[4.2] 准备食品类别节点...")
        graph_data['food_categories'] = []
        for row in table_e1_cleaned:
            category_code = row.get('category_code') or row.get('food_category_code')
            if category_code:
                graph_data['food_categories'].append({
                    'id': category_code,
                    'code': category_code,
                    'name': row.get('category_name') or row.get('food_name'),
                    'level': row.get('level'),
                    'parent_code': row.get('parent_code'),
                    'description': row.get('description'),
                    'source': 'PDF'
                })
        logger.info(f"✓ 准备了{len(graph_data['food_categories'])}个食品类别节点")
        
        # 准备使用关系（转换为图数据库格式）
        logger.info("\n[4.3] 准备使用关系...")
        graph_data['usage_relationships'] = []
        for rel in usage_relationships:
            graph_data['usage_relationships'].append({
                'additive_id': rel['additive_name'],
                'food_code': rel['food_category_code'],
                'max_usage': rel.get('max_usage'),
                'unit': rel.get('unit'),
                'residue_limit': rel.get('residue_limit'),
                'note': rel.get('note'),
                'exception': rel.get('exception', False),
                'source': rel.get('source', 'PDF')
            })
        logger.info(f"✓ 准备了{len(graph_data['usage_relationships'])}个使用关系")
        
        # 准备其他关系
        graph_data['function_relationships'] = function_relationships
        graph_data['exclusion_relationships'] = exclusion_relationships
        graph_data['mixing_relationships'] = mixing_relationships
        
    except Exception as e:
        logger.error(f"准备图数据库数据失败: {e}", exc_info=True)
        return
    
    # 保存图数据库数据
    graph_output_file = OUTPUT_DIR / 'graph_data.json'
    with open(graph_output_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    logger.info(f"\n✓ 图数据库数据已保存至: {graph_output_file}")
    
    # ========== Phase 5: 导入图数据库（可选） ==========
    logger.info("\n" + "=" * 60)
    logger.info("Phase 5: 导入图数据库（可选）")
    logger.info("=" * 60)
    
    import_neo4j = input("\n是否导入Neo4j数据库？(y/n): ").strip().lower()
    
    if import_neo4j == 'y':
        try:
            logger.info("\n[5.1] 连接Neo4j数据库...")
            importer = GraphImporter()
            
            logger.info("\n[5.2] 导入节点和关系...")
            importer.import_from_json(graph_output_file)
            
            logger.info("\n[5.3] 获取统计信息...")
            stats = importer.get_statistics()
            logger.info("\n数据库统计信息:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
            
            importer.close()
            logger.info("\n✓ 数据导入完成！")
            
        except Exception as e:
            logger.error(f"导入Neo4j失败: {e}", exc_info=True)
            logger.info("请检查Neo4j是否启动，以及连接配置是否正确")
    
    # ========== 完成 ==========
    logger.info("\n" + "=" * 60)
    logger.info("数据处理完成！")
    logger.info("=" * 60)
    logger.info("\n输出文件:")
    logger.info(f"  1. 原始数据: {raw_output_file}")
    logger.info(f"  2. 清洗后数据: {cleaned_output_file}")
    logger.info(f"  3. 关系数据: {relationships_output_file}")
    logger.info(f"  4. 图数据库数据: {graph_output_file}")


if __name__ == '__main__':
    main()
