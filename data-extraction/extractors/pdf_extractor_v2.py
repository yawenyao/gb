"""
PDF提取器 V2 - 针对GB 2760-2024的特殊结构优化
"""
import pdfplumber
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import PDF_PATH
from utils.logger import logger


class PDFExtractorV2:
    """PDF提取器 V2 - 优化版"""
    
    def __init__(self, pdf_path: str = PDF_PATH):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
    
    def extract_table_a1(self) -> List[Dict[str, Any]]:
        """
        提取表A.1：食品添加剂使用规定
        
        表A.1的结构：
        - 每个添加剂有标题行：添加剂名称、CNS号、INS号、功能
        - 然后是表格：食品分类号、食品名称、最大使用量、备注
        """
        logger.info("开始提取表A.1（优化版）")
        all_records = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                current_additive = None
                current_cns = None
                current_ins = None
                current_function = None
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # 检查是否在表A.1范围内
                    if '表A.1' not in text and '表A1' not in text:
                        if page_num < 8:  # 表A.1从第8页开始
                            continue
                        if page_num > 200:  # 假设表A.1在200页以内
                            break
                    
                    # 提取文本行
                    lines = text.split('\n')
                    
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        
                        # 跳过表标题行
                        if '表A.1' in line or '表A1' in line or '食品添加剂的允许使用品种' in line:
                            i += 1
                            continue
                        
                        # 检查是否是CNS/INS行（通常在添加剂名称之后）
                        if 'CNS' in line and 'INS' in line:
                            cns_ins = self._extract_cns_ins(line)
                            if cns_ins.get('cns'):
                                current_cns = cns_ins['cns']
                            if cns_ins.get('ins'):
                                current_ins = cns_ins['ins']
                            
                            # CNS/INS行之前通常是添加剂名称（往前查找2-3行）
                            found_name = False
                            for j in range(max(0, i-3), i):
                                prev_line = lines[j].strip()
                                if self._is_additive_name_line(prev_line) and not self._is_food_category_line(prev_line):
                                    additive_info = self._extract_additive_info(prev_line)
                                    name = additive_info.get('name')
                                    # 排除表标题
                                    if name and len(name) > 1 and '食品添加剂' not in name and '允许使用' not in name:
                                        current_additive = name
                                        found_name = True
                                        logger.debug(f"找到添加剂: {current_additive} (CNS: {current_cns}, INS: {current_ins})")
                                        break
                            
                            # 如果没找到，尝试从当前行提取
                            if not found_name and not current_additive:
                                additive_info = self._extract_additive_info(line)
                                name = additive_info.get('name')
                                if name and len(name) > 1 and '食品添加剂' not in name:
                                    current_additive = name
                        
                        # 检查是否是功能行
                        elif '功能' in line and '功能类别' not in line and '功能类别定义' not in line:
                            func = self._extract_function(line)
                            if func and len(func) > 1:
                                current_function = func
                                logger.debug(f"功能: {current_function}")
                        
                        # 识别添加剂标题行（包含中文和英文，且不在表格中）
                        elif self._is_additive_name_line(line) and not self._is_food_category_line(line):
                            # 提取添加剂名称
                            additive_info = self._extract_additive_info(line)
                            name = additive_info.get('name')
                            # 排除表标题和无效名称
                            if name and len(name) > 1 and '食品添加剂' not in name and '允许使用' not in name:
                                # 只有在没有当前添加剂时才更新
                                if not current_additive:
                                    current_additive = name
                                    current_cns = additive_info.get('cns')
                                    current_ins = additive_info.get('ins')
                                    logger.debug(f"找到添加剂: {current_additive}")
                        
                        # 检查是否是表格行（食品分类号格式）
                        elif self._is_food_category_line(line):
                            # 提取使用规定
                            usage = self._extract_usage_from_line(line, current_additive)
                            if usage:
                                usage['cns'] = current_cns
                                usage['ins'] = current_ins
                                usage['function'] = current_function
                                usage['page'] = page_num
                                usage['source'] = 'PDF'
                                all_records.append(usage)
                        
                        i += 1
                    
                    # 也尝试提取表格
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        # 检查表头
                        header_row = table[0]
                        if self._is_usage_table_header(header_row):
                            # 处理数据行
                            for row in table[1:]:
                                if not row or not any(cell for cell in row if cell):
                                    continue
                                
                                usage = self._extract_usage_from_table_row(
                                    row, header_row, current_additive
                                )
                                if usage:
                                    usage['cns'] = current_cns
                                    usage['ins'] = current_ins
                                    usage['function'] = current_function
                                    usage['page'] = page_num
                                    usage['source'] = 'PDF'
                                    all_records.append(usage)
        
        except Exception as e:
            logger.error(f"提取表A.1失败: {e}", exc_info=True)
        
        logger.info(f"表A.1提取完成，共{len(all_records)}条记录")
        return all_records
    
    def _is_additive_name_line(self, line: str) -> bool:
        """判断是否是添加剂名称行"""
        # 包含中文和英文，或者包含CNS/INS标识
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', line))
        has_english = bool(re.search(r'[a-zA-Z]', line))
        return has_chinese and has_english and len(line) > 5
    
    def _extract_additive_info(self, line: str) -> Dict[str, Any]:
        """提取添加剂信息"""
        info = {}
        
        # 排除明显的非添加剂名称行
        exclude_keywords = ['表A', '食品添加剂', '允许使用', '使用范围', '最大使用量', '食品分类号']
        if any(keyword in line for keyword in exclude_keywords):
            return info
        
        # 提取中文名称
        # 格式通常是：中文名 英文名 或 中文名（英文名）
        # 先尝试提取第一个完整的中文词组（不包含"号"、"功能"等）
        chinese_pattern = r'([\u4e00-\u9fff]+(?:[\-\u4e00-\u9fff]+)*)'
        chinese_matches = re.findall(chinese_pattern, line)
        
        if chinese_matches:
            # 过滤掉无效的词
            valid_names = [m for m in chinese_matches 
                          if len(m) > 1 
                          and m not in ['号', '功能', '食品', '名称', '分类', '使用量', '备注']
                          and not m.startswith('CNS')
                          and not m.startswith('INS')]
            
            if valid_names:
                # 取第一个有效的名称（通常是添加剂名称）
                chinese_name = valid_names[0]
                # 进一步清理
                chinese_name = re.sub(r'^[号功能食品名称分类使用量备注]+', '', chinese_name)
                chinese_name = re.sub(r'[号功能食品名称分类使用量备注]+$', '', chinese_name)
                if chinese_name and len(chinese_name) > 1:
                    info['name'] = chinese_name.strip()
        
        # 提取CNS号
        cns_match = re.search(r'CNS\s*(\d+\.?\d*)', line)
        if cns_match:
            info['cns'] = cns_match.group(1)
        
        # 提取INS号
        ins_match = re.search(r'INS\s*(\d+)', line)
        if ins_match:
            info['ins'] = ins_match.group(1)
        
        return info
    
    def _extract_cns_ins(self, line: str) -> Dict[str, str]:
        """提取CNS和INS号"""
        result = {}
        cns_match = re.search(r'CNS\s*(\d+\.?\d*)', line)
        if cns_match:
            result['cns'] = cns_match.group(1)
        ins_match = re.search(r'INS\s*(\d+)', line)
        if ins_match:
            result['ins'] = ins_match.group(1)
        return result
    
    def _extract_function(self, line: str) -> Optional[str]:
        """提取功能"""
        match = re.search(r'功能\s*([\u4e00-\u9fff]+)', line)
        if match:
            return match.group(1)
        return None
    
    def _is_food_category_line(self, line: str) -> bool:
        """判断是否是食品分类号行"""
        # 包含分类号格式：数字.数字
        return bool(re.search(r'\d+\.\d+', line))
    
    def _extract_usage_from_line(self, line: str, additive_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """从文本行提取使用规定"""
        # 这个需要更复杂的解析，暂时返回None
        # 优先使用表格提取
        return None
    
    def _is_usage_table_header(self, header_row: List) -> bool:
        """判断是否是使用规定表格的表头"""
        if not header_row:
            return False
        header_text = ' '.join(str(cell) for cell in header_row if cell)
        keywords = ['食品分类号', '食品名称', '最大使用量', '备注']
        return any(keyword in header_text for keyword in keywords)
    
    def _extract_usage_from_table_row(self, row: List, header_row: List, 
                                     additive_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """从表格行提取使用规定"""
        if not row or len(row) < len(header_row):
            return None
        
        usage = {}
        
        # 映射列
        col_mapping = {}
        for i, header_cell in enumerate(header_row):
            header_str = str(header_cell).strip()
            if '分类号' in header_str:
                col_mapping['food_category_code'] = i
            elif '食品名称' in header_str or '名称' in header_str:
                col_mapping['food_name'] = i
            elif '使用量' in header_str:
                col_mapping['max_usage'] = i
            elif '备注' in header_str:
                col_mapping['note'] = i
        
        # 提取数据
        for key, col_idx in col_mapping.items():
            if col_idx < len(row):
                value = str(row[col_idx]).strip() if row[col_idx] else None
                if value and value != 'None':
                    usage[key] = value
        
        # 必须有添加剂名称和食品分类号
        if additive_name and usage.get('food_category_code'):
            usage['additive_name'] = additive_name
            return usage
        
        return None
