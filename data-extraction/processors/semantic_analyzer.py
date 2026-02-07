"""
语义分析器
"""
import re
from typing import Dict, Any, List, Optional
from utils.logger import logger
from utils.kimi_client import KimiClient


class SemanticAnalyzer:
    """语义分析器"""
    
    def __init__(self):
        self.kimi_client = KimiClient()
    
    def analyze_aggregation(self, text: str) -> List[Dict[str, Any]]:
        """
        分析聚合关系
        
        Args:
            text: 包含分类信息的文本
            
        Returns:
            聚合关系列表
        """
        relationships = []
        
        # 使用正则表达式提取分类层级关系
        # 模式：01.01 包含 01.01.01, 01.01.02 等
        pattern = r'(\d+\.\d+)\s*[包含包括]\s*((?:\d+\.\d+\.\d+(?:\.\d+)?(?:\s*[，,]\s*)?)+)'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            parent_code = match.group(1)
            children_text = match.group(2)
            
            # 提取子分类号
            child_codes = re.findall(r'\d+\.\d+\.\d+(?:\.\d+)?', children_text)
            
            for child_code in child_codes:
                relationships.append({
                    'type': 'aggregation',
                    'parent': parent_code,
                    'child': child_code,
                    'relationship': 'BELONGS_TO'
                })
        
        # 使用AI辅助分析
        if not relationships:
            ai_result = self.kimi_client.analyze_semantic_relationship(text, '聚合关系')
            if ai_result:
                relationships.extend(ai_result.get('relationships', []))
        
        return relationships
    
    def analyze_exclusion(self, text: str) -> List[Dict[str, Any]]:
        """
        分析排除关系
        
        Args:
            text: 包含排除信息的文本
            
        Returns:
            排除关系列表
        """
        relationships = []
        
        # 匹配排除模式
        exclusion_patterns = [
            r'(\d+\.\d+(?:\.\d+)?)\s*除外',
            r'不适用于\s*(\d+\.\d+(?:\.\d+)?)',
            r'例外食品编号[：:]\s*(\d+)',
        ]
        
        for pattern in exclusion_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                excluded_code = match.group(1)
                relationships.append({
                    'type': 'exclusion',
                    'excluded': excluded_code,
                    'relationship': 'EXCLUDED_FROM'
                })
        
        # 使用AI辅助分析
        if not relationships:
            ai_result = self.kimi_client.analyze_semantic_relationship(text, '排除关系')
            if ai_result:
                relationships.extend(ai_result.get('relationships', []))
        
        return relationships
    
    def analyze_reference(self, text: str) -> List[Dict[str, Any]]:
        """
        分析引用关系
        
        Args:
            text: 包含引用信息的文本
            
        Returns:
            引用关系列表
        """
        relationships = []
        
        # 匹配引用模式
        reference_patterns = [
            r'按\s*([^，,。]+)\s*规定',
            r'参照\s*([^，,。]+)',
            r'依据\s*([^，,。]+)',
        ]
        
        for pattern in reference_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                reference = match.group(1)
                relationships.append({
                    'type': 'reference',
                    'reference': reference,
                    'relationship': 'REFERENCED_BY'
                })
        
        # 使用AI辅助分析
        if not relationships:
            ai_result = self.kimi_client.analyze_semantic_relationship(text, '引用关系')
            if ai_result:
                relationships.extend(ai_result.get('relationships', []))
        
        return relationships
    
    def analyze_mixing(self, text: str) -> List[Dict[str, Any]]:
        """
        分析混合使用关系
        
        Args:
            text: 包含混合使用信息的文本
            
        Returns:
            混合关系列表
        """
        relationships = []
        
        # 匹配混合使用模式
        mixing_patterns = [
            r'相同功能.*混合使用.*比例.*和.*不超过\s*(\d+)',
            r'混合使用时.*各自用量.*比例.*和.*不超过\s*(\d+)',
        ]
        
        for pattern in mixing_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                ratio_limit = match.group(1)
                relationships.append({
                    'type': 'mixing',
                    'ratio_limit': ratio_limit,
                    'relationship': 'MIXED_WITH',
                    'condition': f'比例之和不超过{ratio_limit}'
                })
        
        # 使用AI辅助分析
        if not relationships:
            ai_result = self.kimi_client.analyze_semantic_relationship(text, '混合关系')
            if ai_result:
                relationships.extend(ai_result.get('relationships', []))
        
        return relationships
    
    def extract_special_expressions(self, text: str) -> Dict[str, Any]:
        """
        提取特殊表达
        
        Args:
            text: 文本内容
            
        Returns:
            特殊表达字典
        """
        expressions = {
            'unlimited': False,
            'as_needed': False,
            'residue_limit': None,
            'exception': False,
        }
        
        # 检测"按生产需要适量使用"
        if re.search(r'按生产需要适量', text):
            expressions['as_needed'] = True
            expressions['unlimited'] = True
        
        # 检测残留量
        residue_match = re.search(r'残留量[：:]\s*([\d.]+)\s*([a-zA-Z/]+)', text)
        if residue_match:
            expressions['residue_limit'] = {
                'value': residue_match.group(1),
                'unit': residue_match.group(2)
            }
        
        # 检测例外
        if re.search(r'例外|除外', text):
            expressions['exception'] = True
        
        return expressions
