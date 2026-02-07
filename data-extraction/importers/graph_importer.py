"""
图数据库导入器
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OUTPUT_DIR
from utils.logger import logger


class GraphImporter:
    """图数据库导入器"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        self._create_indexes()
    
    def close(self):
        """关闭数据库连接"""
        self.driver.close()
    
    def _create_indexes(self):
        """创建索引"""
        with self.driver.session() as session:
            # 创建节点索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (a:Additive) ON (a.id)",
                "CREATE INDEX IF NOT EXISTS FOR (a:Additive) ON (a.name)",
                "CREATE INDEX IF NOT EXISTS FOR (f:FoodCategory) ON (f.id)",
                "CREATE INDEX IF NOT EXISTS FOR (f:FoodCategory) ON (f.code)",
                "CREATE INDEX IF NOT EXISTS FOR (fc:FunctionCategory) ON (fc.code)",
            ]
            
            for index_query in indexes:
                try:
                    session.run(index_query)
                    logger.info(f"创建索引: {index_query}")
                except Exception as e:
                    logger.warning(f"创建索引失败（可能已存在）: {e}")
    
    def import_additives(self, additives: List[Dict[str, Any]]):
        """
        导入添加剂节点
        
        Args:
            additives: 添加剂数据列表
        """
        logger.info(f"开始导入{len(additives)}个添加剂节点")
        
        with self.driver.session() as session:
            for additive in additives:
                query = """
                MERGE (a:Additive {id: $id})
                SET a.name = $name,
                    a.nameEn = $nameEn,
                    a.casNumber = $casNumber,
                    a.insNumber = $insNumber,
                    a.function = $function,
                    a.source = $source,
                    a.version = $version
                """
                
                session.run(query, {
                    'id': additive.get('id') or additive.get('additive_name'),
                    'name': additive.get('additive_name') or additive.get('name'),
                    'nameEn': additive.get('name_en'),
                    'casNumber': additive.get('cas_number'),
                    'insNumber': additive.get('ins_number'),
                    'function': additive.get('function', []),
                    'source': additive.get('source', 'PDF'),
                    'version': 'GB2760-2024'
                })
        
        logger.info("添加剂节点导入完成")
    
    def import_food_categories(self, categories: List[Dict[str, Any]]):
        """
        导入食品类别节点
        
        Args:
            categories: 食品类别数据列表
        """
        logger.info(f"开始导入{len(categories)}个食品类别节点")
        
        with self.driver.session() as session:
            for category in categories:
                # 创建类别节点
                query = """
                MERGE (f:FoodCategory {id: $id})
                SET f.code = $code,
                    f.name = $name,
                    f.level = $level,
                    f.description = $description,
                    f.source = $source
                """
                
                code = category.get('category_code') or category.get('food_category_code')
                session.run(query, {
                    'id': code,
                    'code': code,
                    'name': category.get('category_name') or category.get('food_name'),
                    'level': category.get('level', self._calculate_level(code)),
                    'description': category.get('description'),
                    'source': category.get('source', 'PDF')
                })
                
                # 创建层级关系
                parent_code = category.get('parent_code') or self._extract_parent_code(code)
                if parent_code:
                    parent_query = """
                    MATCH (child:FoodCategory {code: $child_code})
                    MATCH (parent:FoodCategory {code: $parent_code})
                    MERGE (child)-[:BELONGS_TO]->(parent)
                    """
                    session.run(parent_query, {
                        'child_code': code,
                        'parent_code': parent_code
                    })
        
        logger.info("食品类别节点导入完成")
    
    def import_usage_relationships(self, relationships: List[Dict[str, Any]]):
        """
        导入使用关系
        
        Args:
            relationships: 关系数据列表，包含添加剂和食品类别的使用关系
        """
        logger.info(f"开始导入{len(relationships)}个使用关系")
        
        with self.driver.session() as session:
            for rel in relationships:
                additive_id = rel.get('additive_id') or rel.get('additive_name')
                food_code = rel.get('food_category_code') or rel.get('food_code')
                
                if not additive_id or not food_code:
                    continue
                
                # 判断关系类型
                if rel.get('prohibited', False):
                    query = """
                    MATCH (a:Additive {id: $additive_id})
                    MATCH (f:FoodCategory {code: $food_code})
                    MERGE (a)-[r:PROHIBITED_IN]->(f)
                    SET r.reason = $reason,
                        r.source = $source
                    """
                else:
                    query = """
                    MATCH (a:Additive {id: $additive_id})
                    MATCH (f:FoodCategory {code: $food_code})
                    MERGE (a)-[r:ALLOWED_IN]->(f)
                    SET r.maxUsage = $max_usage,
                        r.unit = $unit,
                        r.residueLimit = $residue_limit,
                        r.note = $note,
                        r.exception = $exception,
                        r.source = $source
                    """
                
                session.run(query, {
                    'additive_id': additive_id,
                    'food_code': food_code,
                    'max_usage': rel.get('max_usage'),
                    'unit': rel.get('unit'),
                    'residue_limit': rel.get('residue_limit'),
                    'note': rel.get('note'),
                    'exception': rel.get('exception', False),
                    'reason': rel.get('reason'),
                    'source': rel.get('source', 'PDF')
                })
        
        logger.info("使用关系导入完成")
    
    def import_function_relationships(self, relationships: List[Dict[str, Any]]):
        """
        导入功能关系
        
        Args:
            relationships: 添加剂与功能类别的关系列表
        """
        logger.info(f"开始导入{len(relationships)}个功能关系")
        
        with self.driver.session() as session:
            for rel in relationships:
                query = """
                MATCH (a:Additive {id: $additive_id})
                MERGE (fc:FunctionCategory {code: $function_code})
                SET fc.name = $function_name
                MERGE (a)-[:HAS_FUNCTION]->(fc)
                """
                
                session.run(query, {
                    'additive_id': rel.get('additive_id') or rel.get('additive_name'),
                    'function_code': rel.get('function_code'),
                    'function_name': rel.get('function_name')
                })
        
        logger.info("功能关系导入完成")
    
    def import_exclusion_relationships(self, relationships: List[Dict[str, Any]]):
        """
        导入排除关系
        
        Args:
            relationships: 排除关系列表
        """
        logger.info(f"开始导入{len(relationships)}个排除关系")
        
        with self.driver.session() as session:
            for rel in relationships:
                query = """
                MATCH (a:Additive {id: $additive_id})
                MATCH (f:FoodCategory {code: $food_code})
                MERGE (a)-[r:EXCLUDED_FROM]->(f)
                SET r.reason = $reason,
                    r.source = $source
                """
                
                session.run(query, {
                    'additive_id': rel.get('additive_id') or rel.get('additive_name'),
                    'food_code': rel.get('food_code') or rel.get('exception_code'),
                    'reason': rel.get('reason', '例外食品'),
                    'source': rel.get('source', 'PDF')
                })
        
        logger.info("排除关系导入完成")
    
    def import_mixing_relationships(self, relationships: List[Dict[str, Any]]):
        """
        导入混合使用关系
        
        Args:
            relationships: 混合使用关系列表
        """
        logger.info(f"开始导入{len(relationships)}个混合使用关系")
        
        with self.driver.session() as session:
            for rel in relationships:
                query = """
                MATCH (a1:Additive {id: $additive1_id})
                MATCH (a2:Additive {id: $additive2_id})
                MERGE (a1)-[r:MIXED_WITH]->(a2)
                SET r.condition = $condition,
                    r.ratioLimit = $ratio_limit,
                    r.source = $source
                """
                
                session.run(query, {
                    'additive1_id': rel.get('additive1_id'),
                    'additive2_id': rel.get('additive2_id'),
                    'condition': rel.get('condition'),
                    'ratio_limit': rel.get('ratio_limit'),
                    'source': rel.get('source', 'PDF')
                })
        
        logger.info("混合使用关系导入完成")
    
    def import_from_json(self, json_file: Path):
        """
        从JSON文件导入数据
        
        Args:
            json_file: JSON文件路径
        """
        logger.info(f"从JSON文件导入数据: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 导入添加剂
        if 'additives' in data:
            self.import_additives(data['additives'])
        
        # 导入食品类别
        if 'food_categories' in data:
            self.import_food_categories(data['food_categories'])
        
        # 导入使用关系
        if 'usage_relationships' in data:
            self.import_usage_relationships(data['usage_relationships'])
        
        # 导入功能关系
        if 'function_relationships' in data:
            self.import_function_relationships(data['function_relationships'])
        
        # 导入排除关系
        if 'exclusion_relationships' in data:
            self.import_exclusion_relationships(data['exclusion_relationships'])
        
        # 导入混合关系
        if 'mixing_relationships' in data:
            self.import_mixing_relationships(data['mixing_relationships'])
        
        logger.info("JSON数据导入完成")
    
    def _calculate_level(self, code: str) -> int:
        """计算分类层级"""
        if not code:
            return 0
        return code.count('.') + 1
    
    def _extract_parent_code(self, code: str) -> Optional[str]:
        """提取父分类号"""
        if not code:
            return None
        last_dot = code.rfind('.')
        if last_dot > 0:
            return code[:last_dot]
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self.driver.session() as session:
            stats = {}
            
            # 节点统计
            node_queries = {
                'additives': 'MATCH (a:Additive) RETURN count(a) as count',
                'food_categories': 'MATCH (f:FoodCategory) RETURN count(f) as count',
                'function_categories': 'MATCH (fc:FunctionCategory) RETURN count(fc) as count',
            }
            
            for key, query in node_queries.items():
                result = session.run(query)
                stats[key] = result.single()['count']
            
            # 关系统计
            rel_queries = {
                'allowed_in': 'MATCH ()-[r:ALLOWED_IN]->() RETURN count(r) as count',
                'prohibited_in': 'MATCH ()-[r:PROHIBITED_IN]->() RETURN count(r) as count',
                'belongs_to': 'MATCH ()-[r:BELONGS_TO]->() RETURN count(r) as count',
                'has_function': 'MATCH ()-[r:HAS_FUNCTION]->() RETURN count(r) as count',
                'excluded_from': 'MATCH ()-[r:EXCLUDED_FROM]->() RETURN count(r) as count',
            }
            
            for key, query in rel_queries.items():
                result = session.run(query)
                stats[key] = result.single()['count']
            
            return stats
