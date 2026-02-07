"""
Kimi API客户端
"""
import json
import requests
from typing import List, Dict, Any, Optional
from config import KIMI_API_KEY, KIMI_BASE_URL
from utils.logger import logger


class KimiClient:
    """Kimi API客户端"""
    
    def __init__(self):
        self.api_key = KIMI_API_KEY
        self.base_url = KIMI_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, messages: List[Dict[str, str]], model: str = "moonshot-v1-32k", temperature: float = 0.3) -> Optional[str]:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            
        Returns:
            API响应内容
        """
        url = f"{self.base_url}/chat/completions"
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Kimi API请求失败: {e}")
            return None
    
    def extract_table_data(self, text: str, table_type: str = "A.1") -> Optional[Dict[str, Any]]:
        """
        从文本中提取表格数据
        
        Args:
            text: 包含表格的文本
            table_type: 表格类型 (A.1, A.2, E.1等)
            
        Returns:
            提取的结构化数据
        """
        prompt = f"""请从以下文本中提取GB 2760-2024标准表{table_type}的数据，并以JSON格式返回。

要求：
1. 识别表格中的所有行和列
2. 提取关键字段（如添加剂名称、食品分类号、最大使用量等）
3. 处理特殊表达（如"按生产需要适量使用"、"除外"、"仅限"等）
4. 识别例外食品编号
5. 返回格式为JSON，包含rows数组，每个元素是一个对象

文本内容：
{text}

请返回JSON格式的数据。"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的数据提取助手，擅长从标准文档中提取结构化数据。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages)
        if not response:
            return None
        
        try:
            # 尝试提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            logger.debug(f"响应内容: {response}")
        
        return None
    
    def analyze_semantic_relationship(self, text: str, relationship_type: str) -> Optional[Dict[str, Any]]:
        """
        分析语义关系
        
        Args:
            text: 需要分析的文本
            relationship_type: 关系类型（聚合、排除、引用、混合等）
            
        Returns:
            识别的关系数据
        """
        prompt = f"""请分析以下文本中的{relationship_type}关系，并以JSON格式返回。

关系类型说明：
- 聚合关系：上级类别包含下级类别（如01.01包含01.01.01）
- 排除关系：明确表示"除外"、"不适用于"等
- 引用关系：引用其他规则或标准
- 混合关系：多个添加剂混合使用的条件

文本内容：
{text}

请返回JSON格式，包含：
- relationship_type: 关系类型
- entities: 涉及的实体列表
- conditions: 条件或限制
- description: 关系描述"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的语义分析助手，擅长识别文本中的语义关系。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages)
        if not response:
            return None
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析语义关系JSON失败: {e}")
        
        return None
    
    def validate_data(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """
        验证和清洗数据
        
        Args:
            data: 待验证的数据
            data_type: 数据类型
            
        Returns:
            验证结果和建议
        """
        prompt = f"""请验证以下{data_type}数据的完整性和准确性，并以JSON格式返回验证结果。

验证项：
1. 必填字段是否完整
2. 数据格式是否正确
3. 数值范围是否合理
4. 是否存在明显错误

数据：
{json.dumps(data, ensure_ascii=False, indent=2)}

请返回JSON格式，包含：
- valid: 是否有效
- errors: 错误列表
- warnings: 警告列表
- suggestions: 改进建议"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的数据验证助手。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages)
        if not response:
            return {"valid": False, "errors": ["API请求失败"]}
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析验证结果失败: {e}")
        
        return {"valid": False, "errors": ["解析失败"]}
