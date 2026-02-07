# GB 2760 食品添加剂基础数据集

数据来源：https://2760.foodmate.net ，经爬取与整理后形成本数据集，用于复刻查询、入库或二次开发。

## 目录结构

- **entities/** 实体表
  - `additives.json` 添加剂主表（faid, name_cn, name_en, cns, ins, function）
  - `categories.json` 食品分类主表（category_code, category_name, limit_id, parent_category_code 层级用）

- **relations/** 关系表
  - `additive_usage.json` 使用关系扁平表：每行一条「某添加剂在某食品分类下的使用规定」，含 faid, food_category_code, food_name, max_usage, remark, usage_type, residue_note；可选 source（本级/上级/GMP：direct/parent/gmp）、unit（从 max_usage 提取的单位）

- **reference/** 附录与参考
  - `processing_aids.json` 加工助剂
  - `enzymes.json` 酶制剂
  - `spices_b1_prohibited.json` 表B.1 不得添加香精香料的食品名单
  - `spices_b2_natural.json` 表B.2 食品用天然香料
  - `spices_b3_synthetic.json` 表B.3 食品用合成香料
  - `spices_rules_principles.json` 香精香料使用原则正文
  - `appendix_d_functions.json` 附录D 功能类别定义
  - `site_rules.json` 首页使用原则

- **index/** 查询索引（便于按添加剂或按分类快速查）
  - `by_additive.json` 按 faid 查：该添加剂在哪些食品分类可用及使用细节
  - `by_category.json` 按 category_code 查：该分类下可用添加剂及使用细则

## 使用方式

- **按添加剂查分类**：`index/by_additive.json[faid].usage`
- **按分类查添加剂**：`index/by_category.json[category_code].additives`
- **关系表统计/入库**：使用 `relations/additive_usage.json` 做分析或导入数据库

## manifest.json

记录各文件条数及说明，见 manifest.json。