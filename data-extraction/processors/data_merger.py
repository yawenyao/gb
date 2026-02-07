"""
数据合并器
合并PDF和网站数据，处理冲突
"""
from typing import List, Dict, Any, Optional
from utils.logger import logger


class DataMerger:
    """数据合并器"""
    
    def __init__(self):
        self.priority_order = ['PDF', 'Announcement', 'Website']  # 优先级顺序
    
    def merge_additives(self, pdf_additives: List[Dict[str, Any]], 
                       web_additives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并添加剂数据
        
        Args:
            pdf_additives: PDF提取的添加剂数据
            web_additives: 网站爬取的添加剂数据
            
        Returns:
            合并后的添加剂数据
        """
        logger.info("合并添加剂数据")
        
        # 以PDF数据为主
        merged = {}
        
        # 添加PDF数据
        for additive in pdf_additives:
            name = additive.get('additive_name') or additive.get('name')
            if name:
                merged[name] = additive.copy()
                merged[name]['sources'] = ['PDF']
        
        # 合并网站数据（补充和验证）
        for additive in web_additives:
            name = additive.get('additive_name') or additive.get('name')
            if not name:
                continue
            
            if name in merged:
                # 合并数据，PDF优先
                merged[name] = self._merge_dict(merged[name], additive, 'PDF', 'Website')
            else:
                # 新增数据
                additive_copy = additive.copy()
                additive_copy['sources'] = ['Website']
                merged[name] = additive_copy
        
        result = list(merged.values())
        logger.info(f"合并完成，共{len(result)}个添加剂")
        return result
    
    def merge_food_categories(self, pdf_categories: List[Dict[str, Any]], 
                             web_categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并食品类别数据
        
        Args:
            pdf_categories: PDF提取的食品类别数据
            web_categories: 网站爬取的食品类别数据
            
        Returns:
            合并后的食品类别数据
        """
        logger.info("合并食品类别数据")
        
        merged = {}
        
        # 添加PDF数据
        for category in pdf_categories:
            code = category.get('category_code') or category.get('food_category_code')
            if code:
                merged[code] = category.copy()
                merged[code]['sources'] = ['PDF']
        
        # 合并网站数据
        for category in web_categories:
            code = category.get('category_code') or category.get('food_category_code')
            if not code:
                continue
            
            if code in merged:
                merged[code] = self._merge_dict(merged[code], category, 'PDF', 'Website')
            else:
                category_copy = category.copy()
                category_copy['sources'] = ['Website']
                merged[code] = category_copy
        
        result = list(merged.values())
        logger.info(f"合并完成，共{len(result)}个食品类别")
        return result
    
    def merge_usage_relationships(self, pdf_relationships: List[Dict[str, Any]], 
                                 web_relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并使用关系数据
        
        Args:
            pdf_relationships: PDF提取的使用关系
            web_relationships: 网站爬取的使用关系
            
        Returns:
            合并后的使用关系
        """
        logger.info("合并使用关系数据")
        
        # 使用组合键去重
        merged = {}
        
        # 添加PDF关系
        for rel in pdf_relationships:
            key = self._get_relationship_key(rel)
            if key:
                merged[key] = rel.copy()
                merged[key]['sources'] = ['PDF']
        
        # 合并网站关系
        for rel in web_relationships:
            key = self._get_relationship_key(rel)
            if not key:
                continue
            
            if key in merged:
                # 检测冲突
                conflict = self._detect_conflict(merged[key], rel)
                if conflict:
                    logger.warning(f"检测到冲突: {key} - {conflict}")
                    # PDF优先
                    merged[key] = self._merge_dict(merged[key], rel, 'PDF', 'Website')
                else:
                    # 合并数据
                    merged[key] = self._merge_dict(merged[key], rel, 'PDF', 'Website')
            else:
                rel_copy = rel.copy()
                rel_copy['sources'] = ['Website']
                merged[key] = rel_copy
        
        result = list(merged.values())
        logger.info(f"合并完成，共{len(result)}个使用关系")
        return result
    
    def detect_conflicts(self, pdf_data: Dict[str, Any], 
                        web_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检测数据冲突
        
        Args:
            pdf_data: PDF数据
            web_data: 网站数据
            
        Returns:
            冲突列表
        """
        logger.info("检测数据冲突")
        conflicts = []
        
        # 检测使用关系冲突
        pdf_rels = pdf_data.get('usage_relationships', [])
        web_rels = web_data.get('usage_relationships', [])
        
        pdf_keys = {self._get_relationship_key(r): r for r in pdf_rels if self._get_relationship_key(r)}
        web_keys = {self._get_relationship_key(r): r for r in web_rels if self._get_relationship_key(r)}
        
        for key in set(pdf_keys.keys()) & set(web_keys.keys()):
            pdf_rel = pdf_keys[key]
            web_rel = web_keys[key]
            
            conflict = self._detect_conflict(pdf_rel, web_rel)
            if conflict:
                conflicts.append({
                    'type': 'usage_relationship',
                    'key': key,
                    'pdf_data': pdf_rel,
                    'web_data': web_rel,
                    'conflict': conflict
                })
        
        logger.info(f"检测到{len(conflicts)}个冲突")
        return conflicts
    
    def _merge_dict(self, base: Dict[str, Any], update: Dict[str, Any], 
                   base_source: str, update_source: str) -> Dict[str, Any]:
        """合并字典，base优先"""
        merged = base.copy()
        
        # 更新数据源
        sources = merged.get('sources', [base_source])
        if update_source not in sources:
            sources.append(update_source)
        merged['sources'] = sources
        
        # 合并字段（base优先，但记录update的值）
        for key, value in update.items():
            if key == 'sources':
                continue
            
            if key not in merged:
                merged[key] = value
            elif merged[key] != value:
                # 记录不同值
                if f'{key}_alt' not in merged:
                    merged[f'{key}_alt'] = {update_source: value}
                else:
                    merged[f'{key}_alt'][update_source] = value
        
        return merged
    
    def _get_relationship_key(self, rel: Dict[str, Any]) -> Optional[str]:
        """获取关系的唯一键"""
        additive = rel.get('additive_name') or rel.get('additive_id')
        food = rel.get('food_category_code') or rel.get('food_code')
        
        if additive and food:
            return f"{additive}::{food}"
        return None
    
    def _detect_conflict(self, pdf_rel: Dict[str, Any], web_rel: Dict[str, Any]) -> Optional[str]:
        """检测关系冲突"""
        conflicts = []
        
        # 检查最大使用量
        pdf_usage = pdf_rel.get('max_usage')
        web_usage = web_rel.get('max_usage')
        
        if pdf_usage and web_usage and pdf_usage != web_usage:
            conflicts.append(f"最大使用量不一致: PDF={pdf_usage}, Website={web_usage}")
        
        # 检查单位
        pdf_unit = pdf_rel.get('unit')
        web_unit = web_rel.get('unit')
        
        if pdf_unit and web_unit and pdf_unit != web_unit:
            conflicts.append(f"单位不一致: PDF={pdf_unit}, Website={web_unit}")
        
        # 检查备注
        pdf_note = pdf_rel.get('note', '')
        web_note = web_rel.get('note', '')
        
        if pdf_note and web_note and pdf_note != web_note:
            # 备注不同不算严重冲突
            pass
        
        return '; '.join(conflicts) if conflicts else None
