# GB 2760-2024 数据提取工具

## 功能概述

本工具用于从PDF标准文档和网站中提取GB 2760-2024食品添加剂使用标准的数据，并进行清洗、语义分析和结构化处理，最终导入图数据库。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

1. 复制 `.env.example` 为 `.env`
2. 配置必要的环境变量：
   - `KIMI_API_KEY`: Kimi API密钥
   - `PDF_PATH`: PDF文件路径
   - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j配置

## 使用方法

### 基本使用

```bash
python main.py
```

### 模块说明

#### 1. PDF提取器 (`extractors/pdf_extractor.py`)
- 提取表A.1（食品添加剂使用规定）
- 提取表A.2（例外食品编号）
- 提取表E.1（食品分类系统）
- 提取章节文本

#### 2. 网站爬虫 (`extractors/web_crawler.py`)
- 爬取添加剂数据
- 爬取食品数据
- 获取详细信息

#### 3. 数据清洗器 (`processors/data_cleaner.py`)
- 清洗添加剂数据
- 清洗食品类别数据
- 标准化单位
- 提取层级关系

#### 4. 语义分析器 (`processors/semantic_analyzer.py`)
- 分析聚合关系
- 分析排除关系
- 分析引用关系
- 分析混合使用关系

#### 5. Kimi客户端 (`utils/kimi_client.py`)
- 表格数据提取
- 语义关系分析
- 数据验证

## 输出文件

提取的数据保存在 `output/` 目录：
- `pdf_data.json`: PDF提取的原始数据
- `cleaned_data.json`: 清洗后的数据
- `relationships.json`: 提取的关系数据

## 注意事项

1. PDF提取可能需要根据实际PDF格式调整
2. 网站爬虫需要遵守robots.txt和使用合理的请求频率
3. AI分析需要API密钥，会产生费用
4. 数据提取后建议人工审核关键数据

## 下一步

数据提取完成后，使用 `graph_importer` 模块将数据导入Neo4j图数据库。
