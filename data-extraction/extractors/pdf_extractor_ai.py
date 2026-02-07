"""
AI增强的PDF提取器
使用AI理解PDF语义，提取完整且正确的数据
"""
import pdfplumber
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from config import PDF_PATH
from utils.logger import logger
from utils.kimi_client import KimiClient


class PDFExtractorAI:
    """AI增强的PDF提取器"""
    
    def __init__(self, pdf_path: str = PDF_PATH):
        self.pdf_path = Path(pdf_path)
        self.kimi_client = KimiClient()
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
    
    def extract_table_with_ai(self, table_name: str = "A.1", use_ai: bool = True) -> List[Dict[str, Any]]:
        """
        使用AI增强提取表格数据
        
        Args:
            table_name: 表格名称 (A.1, A.2, E.1等)
            use_ai: 是否使用AI增强
            
        Returns:
            提取的表格数据
        """
        logger.info(f"开始AI增强提取表{table_name}")
        
        # 步骤1: 使用pdfplumber提取原始表格数据
        raw_tables = self._extract_raw_tables(table_name)
        logger.info(f"步骤1完成: 提取了{len(raw_tables)}个原始表格")
        
        if not raw_tables:
            logger.warning(f"未找到表{table_name}的原始数据")
            return []
        
        # 步骤2: 提取页面文本，用于AI理解上下文
        page_texts = self._extract_page_texts(table_name)
        logger.info(f"步骤2完成: 提取了{len(page_texts)}页文本")
        
        # 步骤3: 使用AI理解和整理数据
        if use_ai:
            ai_enhanced_data = self._ai_enhance_extraction(
                raw_tables, page_texts, table_name
            )
            logger.info(f"步骤3完成: AI增强提取了{len(ai_enhanced_data)}条记录")
            return ai_enhanced_data
        else:
            # 不使用AI，直接处理原始数据
            processed_data = self._process_raw_tables(raw_tables, table_name)
            logger.info(f"步骤4完成: 处理了{len(processed_data)}条记录")
            return processed_data
    
    def _extract_raw_tables(self, table_name: str) -> List[List[List]]:
        """提取原始表格数据"""
        raw_tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    
                    if self._is_target_table(text, table_name):
                        logger.debug(f"在第{page_num}页找到表{table_name}")
                        tables = page.extract_tables()
                        for table in tables:
                            if table and len(table) > 1:  # 至少要有表头和数据行
                                raw_tables.append(table)
        except Exception as e:
            logger.error(f"提取原始表格失败: {e}", exc_info=True)
        
        return raw_tables
    
    def _extract_page_texts(self, table_name: str) -> Dict[int, str]:
        """提取页面文本，用于AI理解上下文"""
        page_texts = {}
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text and self._is_target_table(text, table_name):
                        page_texts[page_num] = text
        except Exception as e:
            logger.error(f"提取页面文本失败: {e}", exc_info=True)
        
        return page_texts
    
    def _ai_enhance_extraction(
        self, 
        raw_tables: List[List[List]], 
        page_texts: Dict[int, str],
        table_name: str
    ) -> List[Dict[str, Any]]:
        """
        使用AI增强数据提取
        
        Args:
            raw_tables: 原始表格数据
            page_texts: 页面文本
            table_name: 表格名称
            
        Returns:
            AI增强后的结构化数据
        """
        all_records = []
        
        # 将表格和文本组合，分批发送给AI
        batch_size = 5  # 每次处理5页
        
        # 按页面组织数据
        page_data = {}
        for i, table in enumerate(raw_tables):
            # 估算表格所在的页面（简化处理）
            page_num = (i // batch_size) + 1
            if page_num not in page_data:
                page_data[page_num] = {
                    'tables': [],
                    'text': page_texts.get(page_num, '')
                }
            page_data[page_num]['tables'].append(table)
        
        # 分批处理
        for page_num, data in page_data.items():
            logger.info(f"使用AI处理第{page_num}页数据...")
            
            # 构建AI提示
            prompt = self._build_ai_prompt(
                data['tables'], 
                data['text'], 
                table_name,
                page_num
            )
            
            # 调用AI
            ai_result = self._call_ai_for_extraction(prompt, table_name)
            
            if ai_result:
                records = self._parse_ai_result(ai_result, table_name, page_num)
                all_records.extend(records)
                logger.info(f"第{page_num}页: AI提取了{len(records)}条记录")
            else:
                # AI失败，使用传统方法
                logger.warning(f"第{page_num}页: AI提取失败，使用传统方法")
                for table in data['tables']:
                    records = self._process_table_traditional(table, table_name, page_num)
                    all_records.extend(records)
        
        return all_records
    
    def _build_ai_prompt(
        self, 
        tables: List[List[List]], 
        page_text: str,
        table_name: str,
        page_num: int
    ) -> str:
        """构建AI提示"""
        
        # 将表格转换为文本格式
        tables_text = []
        for i, table in enumerate(tables):
            table_text = f"表格{i+1}:\n"
            for row in table[:20]:  # 限制行数，避免token过多
                table_text += " | ".join(str(cell) if cell else "" for cell in row) + "\n"
            tables_text.append(table_text)
        
        prompt = f"""你是一个专业的GB 2760-2024标准文档数据提取专家。请从以下PDF页面内容中提取表{table_name}的完整数据。

## 任务要求：
1. **理解表格结构**：识别表头和数据行，理解每列的含义
2. **提取完整数据**：提取所有行数据，包括跨页的数据
3. **理解语义关系**：
   - 识别添加剂名称（可能跨多行）
   - 识别食品分类号和食品名称
   - 识别最大使用量（包括"按生产需要适量使用"等特殊表达）
   - 识别备注中的特殊说明（残留量、例外食品编号等）
4. **处理特殊情况**：
   - 聚合关系：如"各类食品"包含多个子类别
   - 排除关系：如"表A.2中编号为1~68的食品类别除外"
   - 引用关系：引用其他规则或标准
   - 混合使用：相同功能添加剂的混合使用条件

## 页面内容：

### 页面文本：
{page_text[:2000]}  # 限制长度

### 表格数据：
{chr(10).join(tables_text)}

## 输出要求：
请以JSON格式返回提取的数据，格式如下：
{{
  "records": [
    {{
      "additive_name": "添加剂名称",
      "cns": "CNS编号",
      "ins": "INS编号",
      "function": "功能类别",
      "food_category_code": "食品分类号",
      "food_name": "食品名称",
      "max_usage": "最大使用量（数值或'按生产需要适量使用'）",
      "max_usage_value": 数值或null,
      "max_usage_unit": "单位（如g/kg）",
      "note": "备注",
      "as_needed": true/false,
      "residue_limit": "残留量限制（如果有）",
      "exception_codes": ["例外食品编号列表"],
      "page": {page_num}
    }}
  ],
  "relationships": [
    {{
      "type": "聚合/排除/引用/混合",
      "entities": ["相关实体"],
      "description": "关系描述"
    }}
  ],
  "metadata": {{
    "total_records": 记录总数,
    "additives_found": ["发现的添加剂列表"],
    "notes": "提取过程中的注意事项"
  }}
}}

请确保：
1. 提取所有可见的数据行
2. 正确识别添加剂名称（不要将表头或其他文本误识别为添加剂）
3. 正确解析使用量（数值、单位、特殊表达）
4. 提取所有备注信息
5. 识别语义关系"""
        
        return prompt
    
    def _call_ai_for_extraction(self, prompt: str, table_name: str) -> Optional[Dict[str, Any]]:
        """调用AI进行数据提取"""
        messages = [
            {
                "role": "system",
                "content": f"""你是一个专业的GB 2760-2024标准文档数据提取专家。
你擅长：
1. 理解复杂的表格结构
2. 识别食品添加剂的语义关系
3. 提取完整且准确的结构化数据
4. 处理特殊表达和例外情况

请严格按照要求返回JSON格式的数据。"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.kimi_client.chat(messages, model="moonshot-v1-32k", temperature=0.1)
            
            if not response:
                logger.error("AI返回空响应")
                return None
            
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                logger.warning("AI响应中未找到JSON格式数据")
                logger.debug(f"响应内容: {response[:500]}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"解析AI返回的JSON失败: {e}")
            logger.debug(f"响应内容: {response[:1000] if 'response' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"调用AI失败: {e}", exc_info=True)
            return None
    
    def _parse_ai_result(
        self, 
        ai_result: Dict[str, Any], 
        table_name: str,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """解析AI返回的结果"""
        records = []
        
        if 'records' not in ai_result:
            logger.warning("AI结果中缺少records字段")
            return records
        
        for record in ai_result['records']:
            # 标准化记录格式
            standardized = {
                'additive_name': record.get('additive_name', '').strip(),
                'cns': record.get('cns', '').strip(),
                'ins': record.get('ins', '').strip(),
                'function': record.get('function', '').strip(),
                'food_category_code': record.get('food_category_code', '').strip(),
                'food_name': record.get('food_name', '').strip(),
                'max_usage': record.get('max_usage', '').strip(),
                'max_usage_value': record.get('max_usage_value'),
                'max_usage_unit': record.get('max_usage_unit', '').strip(),
                'note': record.get('note', '').strip(),
                'as_needed': record.get('as_needed', False),
                'residue_limit': record.get('residue_limit', '').strip(),
                'exception_codes': record.get('exception_codes', []),
                'page': record.get('page', page_num),
                'source': 'PDF',
                'ai_enhanced': True
            }
            
            # 验证必填字段
            if standardized['additive_name'] and standardized['food_category_code']:
                records.append(standardized)
            else:
                logger.debug(f"跳过不完整的记录: {standardized}")
        
        return records
    
    def _process_raw_tables(
        self, 
        raw_tables: List[List[List]], 
        table_name: str
    ) -> List[Dict[str, Any]]:
        """不使用AI，直接处理原始表格"""
        all_records = []
        
        for table in raw_tables:
            # 估算页面号（简化处理）
            page_num = 1
            records = self._process_table_traditional(table, table_name, page_num)
            all_records.extend(records)
        
        return all_records
    
    def _process_table_traditional(
        self, 
        table: List[List], 
        table_name: str,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """传统方法处理表格（不使用AI）"""
        records = []
        
        if not table or len(table) < 2:
            return records
        
        # 识别表头
        headers = table[0]
        header_map = self._map_headers(headers)
        
        # 处理数据行
        for row in table[1:]:
            if not row or not any(cell for cell in row if cell):
                continue
            
            record = {}
            for i, cell in enumerate(row):
                if i < len(headers) and headers[i]:
                    header_key = header_map.get(i)
                    if header_key:
                        value = str(cell).strip() if cell else ''
                        if value:
                            record[header_key] = value
            
            if record:
                record['page'] = page_num
                record['source'] = 'PDF'
                record['ai_enhanced'] = False
                records.append(record)
        
        return records
    
    def _map_headers(self, headers: List) -> Dict[int, str]:
        """映射表头到字段名"""
        header_map = {}
        header_keywords = {
            '添加剂': 'additive_name',
            '名称': 'additive_name',
            'CNS': 'cns',
            'INS': 'ins',
            '功能': 'function',
            '分类号': 'food_category_code',
            '食品名称': 'food_name',
            '使用量': 'max_usage',
            '备注': 'note'
        }
        
        for i, header in enumerate(headers):
            if not header:
                continue
            
            header_str = str(header).strip()
            for keyword, key in header_keywords.items():
                if keyword in header_str:
                    header_map[i] = key
                    break
        
        return header_map
    
    def _is_target_table(self, text: str, table_name: str) -> bool:
        """判断是否为目标表格"""
        if not text:
            return False
        
        patterns = [
            f'表{table_name}',
            f'表 {table_name}',
            f'表A1' if table_name == 'A.1' else None,
            f'表A2' if table_name == 'A.2' else None,
        ]
        
        for pattern in patterns:
            if pattern and pattern in text:
                return True
        
        return False
    
    def extract_with_ai_validation(
        self, 
        table_name: str = "A.1",
        validate: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        提取数据并使用AI验证
        
        Returns:
            (提取的数据列表, 验证报告)
        """
        # 提取数据
        records = self.extract_table_with_ai(table_name, use_ai=True)
        
        validation_report = {
            'total_records': len(records),
            'valid_records': 0,
            'invalid_records': 0,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        if not validate:
            return records, validation_report
        
        # 使用AI验证数据
        logger.info("使用AI验证提取的数据...")
        
        # 分批验证
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            batch_validation = self._validate_batch(batch, table_name)
            
            validation_report['valid_records'] += batch_validation.get('valid_count', 0)
            validation_report['invalid_records'] += batch_validation.get('invalid_count', 0)
            validation_report['errors'].extend(batch_validation.get('errors', []))
            validation_report['warnings'].extend(batch_validation.get('warnings', []))
            validation_report['suggestions'].extend(batch_validation.get('suggestions', []))
        
        return records, validation_report
    
    def _validate_batch(
        self, 
        records: List[Dict[str, Any]], 
        table_name: str
    ) -> Dict[str, Any]:
        """使用AI验证一批数据"""
        validation_result = {
            'valid_count': 0,
            'invalid_count': 0,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # 构建验证提示
        prompt = f"""请验证以下GB 2760-2024表{table_name}的数据完整性和准确性。

验证项：
1. 必填字段是否完整（添加剂名称、食品分类号）
2. 数据格式是否正确（CNS号、INS号格式）
3. 使用量数值是否合理
4. 是否存在明显错误或遗漏

数据：
{json.dumps(records[:10], ensure_ascii=False, indent=2)}  # 限制数量

请返回JSON格式：
{{
  "valid_count": 有效记录数,
  "invalid_count": 无效记录数,
  "errors": ["错误列表"],
  "warnings": ["警告列表"],
  "suggestions": ["改进建议列表"]
}}"""
        
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的数据验证专家，擅长验证GB 2760标准数据的完整性和准确性。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.kimi_client.chat(messages, temperature=0.1)
            if response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                    return result
        except Exception as e:
            logger.error(f"AI验证失败: {e}")
        
        return validation_result
