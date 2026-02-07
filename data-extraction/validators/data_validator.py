"""
数据验证器
"""
import json
from typing import Dict, Any, List
from pathlib import Path
from utils.logger import logger
from utils.kimi_client import KimiClient


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.kimi_client = KimiClient()
        self.errors = []
        self.warnings = []
    
    def validate_additive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证添加剂数据
        
        Returns:
            验证结果
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 必填字段检查
        required_fields = ['additive_name', 'food_category_code']
        for field in required_fields:
            if not data.get(field):
                result['valid'] = False
                result['errors'].append(f"缺少必填字段: {field}")
        
        # 数据格式检查
        if 'max_usage' in data and data['max_usage']:
            try:
                float(data['max_usage'])
            except (ValueError, TypeError):
                result['warnings'].append(f"最大使用量格式可能不正确: {data['max_usage']}")
        
        # 分类号格式检查
        if 'food_category_code' in data:
            code = data['food_category_code']
            if code and not self._is_valid_category_code(code):
                result['warnings'].append(f"食品分类号格式可能不正确: {code}")
        
        return result
    
    def validate_food_category_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证食品类别数据
        
        Returns:
            验证结果
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 必填字段检查
        code = data.get('category_code') or data.get('food_category_code')
        if not code:
            result['valid'] = False
            result['errors'].append("缺少食品分类号")
        
        # 分类号格式检查
        if code and not self._is_valid_category_code(code):
            result['warnings'].append(f"食品分类号格式可能不正确: {code}")
        
        # 层级一致性检查
        if 'level' in data and code:
            expected_level = code.count('.') + 1
            if data['level'] != expected_level:
                result['warnings'].append(
                    f"层级不一致: 分类号{code}的层级应为{expected_level}，实际为{data['level']}"
                )
        
        return result
    
    def validate_relationships(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证关系数据
        
        Returns:
            验证结果
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {
                'total': len(relationships),
                'valid': 0,
                'invalid': 0
            }
        }
        
        for rel in relationships:
            # 检查必要字段
            if 'additive_name' not in rel or 'food_category_code' not in rel:
                result['errors'].append(f"关系缺少必要字段: {rel}")
                result['statistics']['invalid'] += 1
            else:
                result['statistics']['valid'] += 1
        
        if result['errors']:
            result['valid'] = False
        
        return result
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """
        验证JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            验证结果
        """
        logger.info(f"验证文件: {file_path}")
        
        result = {
            'file': str(file_path),
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证表A.1数据
            if 'table_a1' in data:
                table_a1 = data['table_a1']
                result['statistics']['table_a1'] = len(table_a1)
                
                for i, row in enumerate(table_a1[:10]):  # 只验证前10条
                    validation = self.validate_additive_data(row)
                    if not validation['valid']:
                        result['errors'].extend([f"表A.1第{i+1}行: {e}" for e in validation['errors']])
                    result['warnings'].extend([f"表A.1第{i+1}行: {w}" for w in validation['warnings']])
            
            # 验证表E.1数据
            if 'table_e1' in data:
                table_e1 = data['table_e1']
                result['statistics']['table_e1'] = len(table_e1)
                
                for i, row in enumerate(table_e1[:10]):  # 只验证前10条
                    validation = self.validate_food_category_data(row)
                    if not validation['valid']:
                        result['errors'].extend([f"表E.1第{i+1}行: {e}" for e in validation['errors']])
                    result['warnings'].extend([f"表E.1第{i+1}行: {w}" for w in validation['warnings']])
            
            # 验证关系数据
            if 'usage_relationships' in data:
                relationships = data['usage_relationships']
                validation = self.validate_relationships(relationships)
                result['statistics']['usage_relationships'] = validation['statistics']
                if not validation['valid']:
                    result['errors'].extend(validation['errors'])
                result['warnings'].extend(validation['warnings'])
            
            if result['errors']:
                result['valid'] = False
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"文件读取失败: {e}")
        
        return result
    
    def _is_valid_category_code(self, code: str) -> bool:
        """检查分类号格式是否有效"""
        if not code:
            return False
        
        # 分类号格式：数字.数字.数字（可选更多层级）
        import re
        pattern = r'^\d+(\.\d+)*$'
        return bool(re.match(pattern, str(code)))
    
    def generate_validation_report(self, results: List[Dict[str, Any]], output_file: Path):
        """
        生成验证报告
        
        Args:
            results: 验证结果列表
            output_file: 输出文件路径
        """
        report = {
            'summary': {
                'total_files': len(results),
                'valid_files': sum(1 for r in results if r['valid']),
                'invalid_files': sum(1 for r in results if not r['valid']),
                'total_errors': sum(len(r['errors']) for r in results),
                'total_warnings': sum(len(r['warnings']) for r in results)
            },
            'details': results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"验证报告已保存至: {output_file}")
        
        # 打印摘要
        logger.info("\n验证报告摘要:")
        logger.info(f"  总文件数: {report['summary']['total_files']}")
        logger.info(f"  有效文件: {report['summary']['valid_files']}")
        logger.info(f"  无效文件: {report['summary']['invalid_files']}")
        logger.info(f"  总错误数: {report['summary']['total_errors']}")
        logger.info(f"  总警告数: {report['summary']['total_warnings']}")
