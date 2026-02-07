"""
关系提取器
从清洗后的数据中提取各种关系
"""
from typing import List, Dict, Any
from processors.data_cleaner import DataCleaner
from processors.semantic_analyzer import SemanticAnalyzer
from utils.logger import logger


class RelationshipExtractor:
    """关系提取器"""
    
    def __init__(self):
        self.data_cleaner = DataCleaner()
        self.semantic_analyzer = SemanticAnalyzer()
    
    def extract_usage_relationships(self, table_a1_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从表A.1数据中提取使用关系
        
        Args:
            table_a1_data: 表A.1的数据列表
            
        Returns:
            使用关系列表
        """
        logger.info("提取使用关系")
        relationships = []
        
        for row in table_a1_data:
            additive_name = row.get('additive_name')
            food_category_code = row.get('food_category_code')
            
            if not additive_name or not food_category_code:
                continue
            
            # 检查是否为例外
            note = row.get('note', '')
            is_exception = self.data_cleaner.detect_exception(note)
            exception_code = self.data_cleaner.extract_exception_code(note)
            
            # 提取特殊表达
            special_expr = self.semantic_analyzer.extract_special_expressions(note)
            
            relationship = {
                'additive_name': additive_name,
                'food_category_code': food_category_code,
                'food_name': row.get('food_name'),
                'max_usage': row.get('max_usage'),
                'unit': row.get('unit'),
                'residue_limit': special_expr.get('residue_limit'),
                'note': note,
                'exception': is_exception,
                'exception_code': exception_code,
                'as_needed': special_expr.get('as_needed', False),
                'source': row.get('source', 'PDF')
            }
            
            relationships.append(relationship)
        
        logger.info(f"提取了{len(relationships)}个使用关系")
        return relationships
    
    def extract_category_hierarchy(self, table_e1_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从表E.1数据中提取食品类别层级关系
        
        Args:
            table_e1_data: 表E.1的数据列表
            
        Returns:
            层级关系列表
        """
        logger.info("提取食品类别层级关系")
        relationships = []
        
        for row in table_e1_data:
            category_code = row.get('category_code') or row.get('food_category_code')
            parent_code = row.get('parent_code')
            
            if not category_code:
                continue
            
            # 如果没有父分类号，自动计算
            if not parent_code:
                parent_code = self.data_cleaner._extract_parent_code(category_code)
            
            if parent_code:
                relationship = {
                    'child_code': category_code,
                    'parent_code': parent_code,
                    'child_name': row.get('category_name') or row.get('food_name'),
                    'level': row.get('level', self.data_cleaner._extract_level(category_code)),
                    'source': row.get('source', 'PDF')
                }
                relationships.append(relationship)
        
        logger.info(f"提取了{len(relationships)}个层级关系")
        return relationships
    
    def extract_function_relationships(self, table_a1_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从表A.1数据中提取功能关系
        
        Args:
            table_a1_data: 表A.1的数据列表
            
        Returns:
            功能关系列表
        """
        logger.info("提取功能关系")
        relationships = []
        
        for row in table_a1_data:
            additive_name = row.get('additive_name')
            functions = row.get('function', [])
            
            if not additive_name or not functions:
                continue
            
            # 如果functions是字符串，转换为列表
            if isinstance(functions, str):
                functions = self.data_cleaner._clean_function(functions)
            
            for func in functions:
                relationship = {
                    'additive_name': additive_name,
                    'function_name': func,
                    'function_code': self._get_function_code(func),
                    'source': row.get('source', 'PDF')
                }
                relationships.append(relationship)
        
        logger.info(f"提取了{len(relationships)}个功能关系")
        return relationships
    
    def extract_exclusion_relationships(self, table_a2_data: List[Dict[str, Any]], 
                                       usage_relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从表A.2和表A.1数据中提取排除关系
        
        Args:
            table_a2_data: 表A.2的数据列表（例外食品）
            usage_relationships: 使用关系列表
            
        Returns:
            排除关系列表
        """
        logger.info("提取排除关系")
        relationships = []
        
        # 从表A.2提取例外食品
        exception_codes = {}
        for row in table_a2_data:
            exception_code = row.get('exception_code')
            category_name = row.get('category_name')
            if exception_code:
                exception_codes[exception_code] = category_name
        
        # 从使用关系中提取例外关系
        for rel in usage_relationships:
            if rel.get('exception') and rel.get('exception_code'):
                exception_code = rel['exception_code']
                relationship = {
                    'additive_name': rel['additive_name'],
                    'food_code': rel['food_category_code'],
                    'exception_code': exception_code,
                    'exception_name': exception_codes.get(exception_code),
                    'reason': '例外食品',
                    'source': rel.get('source', 'PDF')
                }
                relationships.append(relationship)
        
        logger.info(f"提取了{len(relationships)}个排除关系")
        return relationships
    
    def extract_mixing_relationships(self, table_a1_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取混合使用关系
        
        Args:
            table_a1_data: 表A.1的数据列表
            
        Returns:
            混合使用关系列表
        """
        logger.info("提取混合使用关系")
        relationships = []
        
        # 按功能分组添加剂（去重）
        function_groups = {}
        for row in table_a1_data:
            additive_name = row.get('additive_name')
            if not additive_name:
                continue
            
            # 获取功能（可能是字符串或列表）
            func = row.get('function')
            if isinstance(func, str):
                func = func.strip()
            elif isinstance(func, list) and func:
                func = func[0] if isinstance(func[0], str) else str(func[0])
            else:
                continue
            
            if not func or len(func) < 2:
                continue
            
            # 只处理特定功能类别（相同色泽着色剂、防腐剂、抗氧化剂）
            mixing_functions = ['着色剂', '防腐剂', '抗氧化剂']
            if func not in mixing_functions:
                continue
            
            if func not in function_groups:
                function_groups[func] = set()
            function_groups[func].add(additive_name)
        
        # 对于相同功能的添加剂，创建混合使用关系
        for func, additives_set in function_groups.items():
            additives = sorted(list(additives_set))  # 排序以确保一致性
            if len(additives) > 1:
                # 创建两两之间的混合关系（限制数量，避免过多）
                max_pairs = 1000  # 限制最大对数
                pair_count = 0
                for i, additive1 in enumerate(additives):
                    for additive2 in additives[i+1:]:
                        if pair_count >= max_pairs:
                            break
                        relationship = {
                            'additive1_name': additive1,
                            'additive2_name': additive2,
                            'function': func,
                            'condition': '相同功能添加剂混合使用时，各自用量占其最大使用量的比例之和不应超过1',
                            'ratio_limit': '1',
                            'source': 'PDF'
                        }
                        relationships.append(relationship)
                        pair_count += 1
                    if pair_count >= max_pairs:
                        break
        
        logger.info(f"提取了{len(relationships)}个混合使用关系")
        return relationships
    
    def _get_function_code(self, function_name: str) -> str:
        """获取功能类别代码"""
        # 功能类别代码映射（可以根据实际标准补充）
        function_code_map = {
            '防腐剂': '01',
            '抗氧化剂': '02',
            '着色剂': '03',
            '护色剂': '04',
            '乳化剂': '05',
            '增稠剂': '06',
            '稳定剂': '07',
            '甜味剂': '08',
            '酸度调节剂': '09',
            '抗结剂': '10',
            '消泡剂': '11',
            '漂白剂': '12',
            '膨松剂': '13',
            '胶基糖果中基础剂物质': '14',
            '着色剂': '15',
            '护色剂': '16',
            '酶制剂': '17',
            '增味剂': '18',
            '面粉处理剂': '19',
            '被膜剂': '20',
            '水分保持剂': '21',
            '营养强化剂': '22',
            '防腐剂': '23',
            '稳定和凝固剂': '24',
            '甜味剂': '25',
            '增稠剂': '26',
            '食品用香料': '27',
            '食品工业用加工助剂': '28',
        }
        
        return function_code_map.get(function_name, function_name)
