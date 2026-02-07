"""
配置管理模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量：优先加载 data-extraction 目录下的 .env，再加载项目根目录
DATA_EXTRACTION_ROOT = Path(__file__).parent
PROJECT_ROOT = DATA_EXTRACTION_ROOT.parent
load_dotenv(DATA_EXTRACTION_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")

# 项目根目录（已在上面定义）

# API配置
KIMI_API_KEY = os.environ.get('KIMI_API_KEY', 'sk-qEX7VqCvSmliU3YW4Wal0VXdVdLeAbu61VcAtwwYggQs63vf')
KIMI_BASE_URL = os.environ.get('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Neo4j配置
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'neo4j')

# 文件路径
PDF_PATH = os.environ.get('PDF_PATH', str(PROJECT_ROOT / 'GB 2760-2024 食品安全国家标准　食品添加剂使用标准(3).pdf'))
OUTPUT_DIR = Path(os.environ.get('OUTPUT_DIR', str(DATA_EXTRACTION_ROOT / 'output')))
CACHE_DIR = Path(os.environ.get('CACHE_DIR', str(DATA_EXTRACTION_ROOT / 'cache')))

# 创建输出目录
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 网站配置
WEBSITE_BASE_URL = 'https://2760.foodmate.net'
WEBSITE_SEARCH_URL = f'{WEBSITE_BASE_URL}/search'

# 请求配置
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1  # 请求间隔（秒）

# 数据提取配置
BATCH_SIZE = 100  # 批量处理大小
MAX_RETRIES = 3  # 最大重试次数
