"""
PDF提取器
"""
import pdfplumber
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import PDF_PATH
from utils.logger import logger
from utils.kimi_client import KimiClient


class PDFExtractor:
    """PDF提取器"""
    
    def __init__(self, pdf_path: str = PDF_PATH):
        self.pdf_path = Path(pdf_path)
        self.kimi_client = KimiClient()
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
    
    def extract_tables(self, table_name: str = "A.1") -> List[Dict[str, Any]]:
        """
        提取指定表格
        
        Args:
            table_name: 表格名称 (A.1, A.2, E.1等)
            
        Returns:
            提取的表格数据
        """
        logger.info(f"开始提取表{table_name}")
        tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # 提取页面文本，用于定位表格
                    text = page.extract_text()
                    
                    # 查找目标表格
                    if self._is_target_table(text, table_name):
                        logger.info(f"在第{page_num}页找到表{table_name}")
                        
                        # 提取表格
                        page_tables = page.extract_tables()
                        for table in page_tables:
                            if table:
                                processed_table = self._process_table(table, table_name, page_num)
                                if processed_table:
                                    tables.extend(processed_table)
        
        except Exception as e:
            logger.error(f"提取表{table_name}失败: {e}")
        
        logger.info(f"表{table_name}提取完成，共{len(tables)}条记录")
        return tables
    
    def _is_target_table(self, text: str, table_name: str) -> bool:
        """判断是否为目标表格"""
        patterns = [
            f"表{table_name}",
            f"表 {table_name}",
            f"表A{table_name.replace('A.', '')}" if table_name.startswith('A.') else None,
        ]
        for pattern in patterns:
            if pattern and pattern in text:
                return True
        # 表E.1 仅匹配附录E中的表格页（表E1/表E.1），避免匹配目录中的“食品分类系统”
        if table_name == "E.1":
            if "表E1" in text or "表E.1" in text or ("附录 E" in text and "食品分类号" in text):
                return True
        return False
    
    def _process_table(self, table: List[List], table_name: str, page_num: int) -> List[Dict[str, Any]]:
        """
        处理表格数据
        
        Args:
            table: 原始表格数据
            table_name: 表格名称
            page_num: 页码
            
        Returns:
            处理后的数据列表
        """
        if not table or len(table) < 2:
            return []
        
        # 根据表格类型选择不同的处理方式
        if table_name == "A.1":
            return self._process_table_a1(table, page_num)
        elif table_name == "A.2":
            return self._process_table_a2(table, page_num)
        elif table_name == "E.1":
            return self._process_table_e1(table, page_num)
        else:
            return self._process_generic_table(table, table_name, page_num)
    
    def _process_table_a1(self, table: List[List], page_num: int) -> List[Dict[str, Any]]:
        """处理表A.1：食品添加剂使用规定"""
        rows = []
        headers = None
        additive_name = None  # 添加剂名称可能在多行中
        
        for i, row in enumerate(table):
            if not row or not any(cell for cell in row if cell):
                continue
            
            # 识别表头
            if i == 0 or (headers is None and self._is_header_row(row)):
                headers = self._normalize_headers(row)
                # 检查是否有添加剂名称列
                if headers and 'additive_name' not in headers:
                    # 尝试从第一列识别添加剂名称
                    for idx, header in enumerate(headers):
                        if not header or header == '':
                            # 第一列可能是添加剂名称
                            headers[idx] = 'additive_name'
                            break
                continue
            
            if headers is None:
                continue
            
            # 处理数据行
            row_data = {}
            
            # 检查第一列是否是添加剂名称（通常第一列是序号或添加剂名称）
            first_cell = self._clean_cell(row[0]) if row else None
            if first_cell:
                # 如果第一列不是数字且不是分类号格式，可能是添加剂名称
                if not first_cell.replace('.', '').isdigit() and not re.match(r'^\d+\.\d+', first_cell):
                    # 可能是添加剂名称
                    if 'additive_name' not in row_data:
                        row_data['additive_name'] = first_cell
                        additive_name = first_cell  # 保存当前添加剂名称
                    # 从第二列开始处理
                    start_col = 1
                else:
                    # 第一列是序号或分类号，使用保存的添加剂名称
                    if additive_name:
                        row_data['additive_name'] = additive_name
                    start_col = 0
            else:
                # 使用保存的添加剂名称
                if additive_name:
                    row_data['additive_name'] = additive_name
                start_col = 0
            
            # 处理其他列
            for j in range(start_col, len(row)):
                col_idx = j - start_col if start_col > 0 else j
                if col_idx < len(headers) and headers[col_idx]:
                    value = self._clean_cell(row[j])
                    if value:
                        row_data[headers[col_idx]] = value
            
            # 如果没有添加剂名称，尝试从其他列推断
            if 'additive_name' not in row_data or not row_data['additive_name']:
                # 检查是否有包含添加剂名称的列
                for key, value in row_data.items():
                    if value and isinstance(value, str):
                        # 如果值很长且不像是分类号或使用量，可能是添加剂名称
                        if len(value) > 5 and not re.match(r'^[\d.]+', value) and 'g/kg' not in value.lower():
                            row_data['additive_name'] = value
                            additive_name = value
                            break
            
            if row_data:
                row_data['page'] = page_num
                row_data['source'] = 'PDF'
                rows.append(row_data)
        
        return rows
    
    def _process_table_a2(self, table: List[List], page_num: int) -> List[Dict[str, Any]]:
        """处理表A.2：例外食品编号"""
        rows = []
        headers = None
        
        for i, row in enumerate(table):
            if not row or not any(cell for cell in row if cell):
                continue
            
            if i == 0:
                headers = self._normalize_headers(row)
                continue
            
            if headers is None:
                continue
            
            row_data = {}
            for j, cell in enumerate(row):
                if j < len(headers) and headers[j]:
                    value = self._clean_cell(cell)
                    if value:
                        row_data[headers[j]] = value
            
            if row_data:
                row_data['page'] = page_num
                row_data['source'] = 'PDF'
                rows.append(row_data)
        
        return rows
    
    def _process_table_e1(self, table: List[List], page_num: int) -> List[Dict[str, Any]]:
        """处理表E.1：食品分类系统"""
        rows = []
        headers = None
        
        for i, row in enumerate(table):
            if not row or not any(cell for cell in row if cell):
                continue
            
            if i == 0:
                headers = self._normalize_headers(row)
                continue
            
            if headers is None:
                continue
            
            row_data = {}
            for j, cell in enumerate(row):
                if j < len(headers) and headers[j]:
                    value = self._clean_cell(cell)
                    if value:
                        row_data[headers[j]] = value
            
            if row_data:
                # 统一字段名：category_code / food_category_code 都保留
                if 'category_code' not in row_data and 'food_category_code' in row_data:
                    row_data['category_code'] = row_data['food_category_code']
                if 'category_code' in row_data and 'food_category_code' not in row_data:
                    row_data['food_category_code'] = row_data['category_code']
                row_data['page'] = page_num
                row_data['source'] = 'PDF'
                rows.append(row_data)
        
        return rows
    
    def _process_generic_table(self, table: List[List], table_name: str, page_num: int) -> List[Dict[str, Any]]:
        """处理通用表格"""
        rows = []
        headers = None
        
        for i, row in enumerate(table):
            if not row or not any(cell for cell in row if cell):
                continue
            
            if i == 0:
                headers = self._normalize_headers(row)
                continue
            
            if headers is None:
                continue
            
            row_data = {}
            for j, cell in enumerate(row):
                if j < len(headers) and headers[j]:
                    value = self._clean_cell(cell)
                    if value:
                        row_data[headers[j]] = value
            
            if row_data:
                row_data['page'] = page_num
                row_data['source'] = 'PDF'
                rows.append(row_data)
        
        return rows
    
    def _is_header_row(self, row: List) -> bool:
        """判断是否为表头行"""
        if not row:
            return False
        
        header_keywords = ['序号', '名称', '功能', '分类', '使用量', '备注', '编号']
        row_text = ' '.join(str(cell) for cell in row if cell)
        return any(keyword in row_text for keyword in header_keywords)
    
    def _normalize_headers(self, row: List) -> List[str]:
        """标准化表头"""
        headers = []
        header_mapping = {
            '序号': 'serial_number',
            '食品添加剂名称': 'additive_name',
            '功能': 'function',
            '食品分类号': 'food_category_code',
            '食品名称': 'food_name',
            '最大使用量': 'max_usage',
            '最大使用量/(g/kg)': 'max_usage',
            '最大使用量\n/(g/kg)': 'max_usage',
            '备注': 'note',
            '例外食品编号': 'exception_code',
            '例外食品类别编号': 'exception_code',
            '食品类别名称': 'category_name',
            '说明': 'description',
            '分类号': 'category_code',
            '类别': 'category_name',
        }
        
        for cell in row:
            if not cell:
                headers.append('')
                continue
            
            cell_str = str(cell).strip()
            # 移除换行符和多余空白
            cell_str = cell_str.replace('\n', ' ').replace('\r', ' ')
            cell_str = ' '.join(cell_str.split())
            
            # 查找映射（精确匹配或包含匹配）
            header = None
            for key, value in header_mapping.items():
                if key in cell_str or cell_str in key:
                    header = value
                    break
            
            if not header:
                # 尝试模糊匹配
                cell_lower = cell_str.lower()
                if '添加剂' in cell_str or '名称' in cell_str:
                    header = 'additive_name'
                elif '分类号' in cell_str or '分类' in cell_str:
                    header = 'food_category_code'
                elif '食品名称' in cell_str or ('食品' in cell_str and '名称' in cell_str):
                    header = 'food_name'
                elif '使用量' in cell_str or '用量' in cell_str:
                    header = 'max_usage'
                elif '功能' in cell_str:
                    header = 'function'
                elif '备注' in cell_str:
                    header = 'note'
                else:
                    # 默认处理：转换为小写并替换空格
                    header = cell_lower.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
            
            headers.append(header)
        
        return headers
    
    def _clean_cell(self, cell: Any) -> Optional[str]:
        """清洗单元格内容"""
        if cell is None:
            return None
        
        text = str(cell).strip()
        if not text or text == '':
            return None
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def extract_text_by_section(self, section_name: str) -> Optional[str]:
        """
        按章节提取文本
        
        Args:
            section_name: 章节名称（如"第3章"、"附录A"）
            
        Returns:
            提取的文本内容
        """
        logger.info(f"提取章节: {section_name}")
        text_parts = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                in_section = False
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if not page_text:
                        continue
                    
                    # 检测章节开始
                    if section_name in page_text:
                        in_section = True
                    
                    if in_section:
                        text_parts.append(page_text)
                        
                        # 检测章节结束（遇到下一个章节）
                        if self._is_next_section(page_text, section_name):
                            break
        
        except Exception as e:
            logger.error(f"提取章节{section_name}失败: {e}")
        
        return '\n'.join(text_parts) if text_parts else None
    
    def _is_next_section(self, text: str, current_section: str) -> bool:
        """判断是否到了下一个章节"""
        # 简单的章节检测逻辑
        section_patterns = [
            r'第\d+章',
            r'附录[A-Z]',
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, text)
            if len(matches) > 1:  # 如果找到多个章节标记
                return True
        
        return False
