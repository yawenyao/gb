"""
数据清洗器
"""
import re
from typing import Dict, Any, List, Optional
from utils.logger import logger


class DataCleaner:
    """数据清洗器"""
    
    # 单位映射
    UNIT_MAPPING = {
        'g/kg': 'g/kg',
        'mg/kg': 'mg/kg',
        'g/L': 'g/L',
        'mg/L': 'mg/L',
        '按生产需要适量使用': '适量',
        '按生产需要适量添加': '适量',
    }
    
    # 特殊值处理
    SPECIAL_VALUES = {
        '按生产需要适量使用': None,
        '按生产需要适量添加': None,
        '适量': None,
        '—': None,
        '无': None,
    }
    
    def clean_additive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗添加剂数据
        
        Args:
            data: 原始数据
            
        Returns:
            清洗后的数据
        """
        cleaned = data.copy()
        
        # 清洗名称
        if 'additive_name' in cleaned:
            cleaned['additive_name'] = self._clean_name(cleaned['additive_name'])
        
        # 清洗功能
        if 'function' in cleaned:
            cleaned['function'] = self._clean_function(cleaned['function'])
        
        # 清洗使用量
        if 'max_usage' in cleaned:
            cleaned['max_usage'], cleaned['unit'] = self._clean_usage(cleaned['max_usage'])
        
        # 清洗食品分类号
        if 'food_category_code' in cleaned:
            cleaned['food_category_code'] = self._clean_category_code(cleaned['food_category_code'])
        
        # 清洗备注
        if 'note' in cleaned:
            cleaned['note'] = self._clean_note(cleaned['note'])
        
        return cleaned
    
    def clean_food_category_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗食品类别数据
        
        Args:
            data: 原始数据
            
        Returns:
            清洗后的数据
        """
        cleaned = data.copy()
        
        # 清洗分类号
        if 'category_code' in cleaned:
            cleaned['category_code'] = self._clean_category_code(cleaned['category_code'])
        
        # 清洗名称
        if 'category_name' in cleaned:
            cleaned['category_name'] = self._clean_name(cleaned['category_name'])
        
        # 提取层级
        if 'category_code' in cleaned:
            cleaned['level'] = self._extract_level(cleaned['category_code'])
            cleaned['parent_code'] = self._extract_parent_code(cleaned['category_code'])
        
        return cleaned
    
    def _clean_name(self, name: str) -> str:
        """清洗名称"""
        if not name:
            return ''
        
        # 移除多余空白
        name = re.sub(r'\s+', ' ', str(name)).strip()
        
        # 移除特殊字符
        name = re.sub(r'[^\w\s\u4e00-\u9fff\-\(\)]', '', name)
        
        return name
    
    def _clean_function(self, function: str) -> List[str]:
        """清洗功能类别"""
        if not function:
            return []
        
        # 分割功能类别
        functions = re.split(r'[，,、;；]', str(function))
        
        # 清洗每个功能
        cleaned_functions = []
        for func in functions:
            func = func.strip()
            if func:
                cleaned_functions.append(func)
        
        return cleaned_functions
    
    def _clean_usage(self, usage: str) -> tuple[Optional[str], Optional[str]]:
        """
        清洗使用量
        
        Returns:
            (数值, 单位)
        """
        if not usage:
            return None, None
        
        usage_str = str(usage).strip()
        
        # 检查特殊值
        if usage_str in self.SPECIAL_VALUES:
            return None, '适量'
        
        # 提取数值和单位
        # 匹配模式：数字 + 单位
        pattern = r'([\d.]+)\s*([a-zA-Z/]+)'
        match = re.search(pattern, usage_str)
        
        if match:
            value = match.group(1)
            unit = match.group(2)
            
            # 标准化单位
            unit = self.UNIT_MAPPING.get(unit.lower(), unit)
            
            return value, unit
        
        # 尝试提取纯数字
        number_match = re.search(r'[\d.]+', usage_str)
        if number_match:
            return number_match.group(), None
        
        return None, None
    
    def _clean_category_code(self, code: str) -> str:
        """清洗食品分类号"""
        if not code:
            return ''
        
        code_str = str(code).strip()
        
        # 移除非数字和点的字符
        code_str = re.sub(r'[^\d.]', '', code_str)
        
        return code_str
    
    def _extract_level(self, code: str) -> int:
        """提取层级"""
        if not code:
            return 0
        
        # 计算点的数量 + 1
        return code.count('.') + 1
    
    def _extract_parent_code(self, code: str) -> Optional[str]:
        """提取父分类号"""
        if not code:
            return None
        
        # 找到最后一个点
        last_dot = code.rfind('.')
        if last_dot > 0:
            return code[:last_dot]
        
        return None
    
    def _clean_note(self, note: str) -> str:
        """清洗备注"""
        if not note:
            return ''
        
        note_str = str(note).strip()
        
        # 移除多余空白
        note_str = re.sub(r'\s+', ' ', note_str)
        
        return note_str
    
    def detect_exception(self, note: str) -> bool:
        """检测是否为例外食品"""
        if not note:
            return False
        
        exception_keywords = ['例外', '除外', '不适用于', '仅限']
        return any(keyword in note for keyword in exception_keywords)
    
    def extract_exception_code(self, note: str) -> Optional[str]:
        """提取例外食品编号"""
        if not note:
            return None
        
        # 匹配模式：例外食品编号 + 数字
        pattern = r'例外食品编号[：:]\s*(\d+)'
        match = re.search(pattern, note)
        
        if match:
            return match.group(1)
        
        return None
