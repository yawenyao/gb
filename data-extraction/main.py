"""
主程序入口
"""
import json
from pathlib import Path
from extractors.pdf_extractor import PDFExtractor
from extractors.web_crawler import WebCrawler
from processors.data_cleaner import DataCleaner
from processors.semantic_analyzer import SemanticAnalyzer
from config import OUTPUT_DIR
from utils.logger import logger


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("GB 2760-2024 数据提取工具")
    logger.info("=" * 60)
    
    # 初始化组件
    pdf_extractor = PDFExtractor()
    web_crawler = WebCrawler()
    data_cleaner = DataCleaner()
    semantic_analyzer = SemanticAnalyzer()
    
    # 1. 提取PDF数据
    logger.info("\n[步骤1] 提取PDF数据")
    pdf_data = {}
    
    try:
        # 提取表A.1
        logger.info("提取表A.1...")
        table_a1 = pdf_extractor.extract_tables("A.1")
        pdf_data['table_a1'] = table_a1
        logger.info(f"表A.1提取完成，共{len(table_a1)}条记录")
        
        # 提取表A.2
        logger.info("提取表A.2...")
        table_a2 = pdf_extractor.extract_tables("A.2")
        pdf_data['table_a2'] = table_a2
        logger.info(f"表A.2提取完成，共{len(table_a2)}条记录")
        
        # 提取表E.1
        logger.info("提取表E.1...")
        table_e1 = pdf_extractor.extract_tables("E.1")
        pdf_data['table_e1'] = table_e1
        logger.info(f"表E.1提取完成，共{len(table_e1)}条记录")
        
    except Exception as e:
        logger.error(f"PDF提取失败: {e}")
    
    # 2. 清洗PDF数据
    logger.info("\n[步骤2] 清洗PDF数据")
    cleaned_pdf_data = {}
    
    for table_name, table_data in pdf_data.items():
        cleaned_table = []
        for row in table_data:
            if table_name == 'table_a1':
                cleaned_row = data_cleaner.clean_additive_data(row)
            elif table_name == 'table_e1':
                cleaned_row = data_cleaner.clean_food_category_data(row)
            else:
                cleaned_row = row
            
            cleaned_table.append(cleaned_row)
        
        cleaned_pdf_data[table_name] = cleaned_table
        logger.info(f"{table_name}清洗完成，共{len(cleaned_table)}条记录")
    
    # 3. 保存PDF数据
    logger.info("\n[步骤3] 保存PDF数据")
    pdf_output_file = OUTPUT_DIR / 'pdf_data.json'
    with open(pdf_output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_pdf_data, f, ensure_ascii=False, indent=2)
    logger.info(f"PDF数据已保存至: {pdf_output_file}")
    
    # 4. 爬取网站数据（可选，需要时启用）
    logger.info("\n[步骤4] 爬取网站数据（跳过，需要时启用）")
    # web_data = {}
    # try:
    #     additives = web_crawler.crawl_all_additives()
    #     web_data['additives'] = additives
    #     logger.info(f"网站数据爬取完成，共{len(additives)}条记录")
    # except Exception as e:
    #     logger.error(f"网站爬取失败: {e}")
    
    # 5. 语义分析（示例）
    logger.info("\n[步骤5] 语义分析")
    # 这里可以添加语义分析的示例代码
    
    logger.info("\n" + "=" * 60)
    logger.info("数据提取完成！")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
