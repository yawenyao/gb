package com.gb2760.loader;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.data.neo4j.core.Neo4jClient;
import org.springframework.stereotype.Component;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/**
 * 将 foodmate_dataset 下的 entities/relations 导入 Neo4j。
 * 使用方式：--spring.profiles.active=import 或 gb2760.import-on-startup=true
 */
@Slf4j
@Component
@RequiredArgsConstructor
@Profile("import")
public class Neo4jDataLoader implements ApplicationRunner {

    private final Neo4jClient neo4jClient;
    private final ObjectMapper objectMapper;

    @Value("${dataset.path:}")
    private String datasetPath;

    @Value("${gb2760.import-only:false}")
    private boolean importOnly;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        if (datasetPath == null || datasetPath.isBlank()) {
            log.warn("dataset.path 未配置，跳过导入");
            return;
        }
        Path base = Path.of(datasetPath);
        if (!Files.isDirectory(base)) {
            log.warn("dataset.path 不是目录: {}", base);
            return;
        }

        log.info("开始导入 Neo4j: {}", base);

        // 1) 清空现有数据（按需）
        neo4jClient.query("MATCH (n) DETACH DELETE n").run();

        // 2) 导入 Category
        Path categoriesPath = base.resolve("entities/categories.json");
        if (Files.exists(categoriesPath)) {
            List<Map<String, Object>> categories = objectMapper.readValue(
                    Files.newInputStream(categoriesPath), new TypeReference<>() {});
            for (Map<String, Object> c : categories) {
                String code = (String) c.get("category_code");
                String name = (String) c.get("category_name");
                Object limitId = c.get("limit_id");
                if (code == null) continue;
                neo4jClient.query(
                        "MERGE (c:Category {categoryCode: $code}) SET c.categoryName = $name, c.limitId = $limitId"
                ).bind(code).to("code").bind(name).to("name").bind(limitId != null ? ((Number) limitId).intValue() : null).to("limitId").run();
            }
            log.info("导入 Category 数量: {}", categories.size());
        }

        // 3) 导入 Additive
        Path additivesPath = base.resolve("entities/additives.json");
        if (Files.exists(additivesPath)) {
            List<Map<String, Object>> additives = objectMapper.readValue(
                    Files.newInputStream(additivesPath), new TypeReference<>() {});
            for (Map<String, Object> a : additives) {
                Object faidObj = a.get("faid");
                if (faidObj == null) continue;
                long faid = ((Number) faidObj).longValue();
                String nameCn = (String) a.get("name_cn");
                String nameEn = (String) a.get("name_en");
                String cns = (String) a.get("cns");
                String ins = (String) a.get("ins");
                String function = (String) a.get("function");
                neo4jClient.query(
                        "MERGE (a:Additive {faid: $faid}) SET a.nameCn = $nameCn, a.nameEn = $nameEn, a.cns = $cns, a.ins = $ins, a.function = $function"
                ).bind(faid).to("faid")
                        .bind(nameCn).to("nameCn").bind(nameEn).to("nameEn")
                        .bind(cns).to("cns").bind(ins).to("ins").bind(function).to("function").run();
            }
            log.info("导入 Additive 数量: {}", additives.size());
        }

        // 4) 导入 USED_IN：先确保出现的 food_category_code 都有 Category 节点
        Path usagePath = base.resolve("relations/additive_usage.json");
        if (Files.exists(usagePath)) {
            List<Map<String, Object>> usages = objectMapper.readValue(
                    Files.newInputStream(usagePath), new TypeReference<>() {});
            int created = 0;
            for (Map<String, Object> u : usages) {
                Object faidObj = u.get("faid");
                String foodCategoryCode = (String) u.get("food_category_code");
                String foodName = (String) u.get("food_name");
                String maxUsage = (String) u.get("max_usage");
                String remark = (String) u.get("remark");
                String usageType = (String) u.get("usage_type");
                String residueNote = (String) u.get("residue_note");
                String source = (String) u.get("source");
                String unit = (String) u.get("unit");
                if (faidObj == null || foodCategoryCode == null) continue;
                long faid = ((Number) faidObj).longValue();
                // 确保 Category 存在（如 "—" 可能不在 categories.json 中）
                neo4jClient.query(
                        "MERGE (c:Category {categoryCode: $code}) ON CREATE SET c.categoryName = $name"
                ).bind(foodCategoryCode).to("code").bind(foodName != null ? foodName : foodCategoryCode).to("name").run();
                neo4jClient.query(
                        "MATCH (a:Additive {faid: $faid}), (c:Category {categoryCode: $code}) " +
                                "MERGE (a)-[r:USED_IN]->(c) SET r.foodCategoryCode = $code, r.foodName = $foodName, r.maxUsage = $maxUsage, r.remark = $remark, r.usageType = $usageType, r.residueNote = $residueNote, r.source = $source, r.unit = $unit"
                ).bind(faid).to("faid").bind(foodCategoryCode).to("code")
                        .bind(foodName).to("foodName").bind(maxUsage).to("maxUsage")
                        .bind(remark).to("remark").bind(usageType).to("usageType").bind(residueNote).to("residueNote")
                        .bind(source).to("source").bind(unit).to("unit").run();
                created++;
            }
            log.info("导入 USED_IN 数量: {}", created);
        }

        // 5) 建立分类层级：Category -[:BELONGS_TO]-> Category（子指向父）
        if (Files.exists(categoriesPath)) {
            List<Map<String, Object>> categories = objectMapper.readValue(
                    Files.newInputStream(categoriesPath), new TypeReference<>() {});
            int hierarchyEdges = 0;
            for (Map<String, Object> c : categories) {
                String code = (String) c.get("category_code");
                String parentCode = (String) c.get("parent_category_code");
                if (code == null || parentCode == null || parentCode.isBlank()) continue;
                var runResult = neo4jClient.query(
                        "MATCH (child:Category {categoryCode: $childCode}), (parent:Category {categoryCode: $parentCode}) " +
                                "MERGE (child)-[:BELONGS_TO]->(parent)"
                ).bind(code).to("childCode").bind(parentCode).to("parentCode").run();
                hierarchyEdges++;
            }
            if (hierarchyEdges > 0) {
                log.info("导入 BELONGS_TO 层级边数量: {}", hierarchyEdges);
            }
        }

        log.info("Neo4j 导入完成");
        if (importOnly) {
            log.info("仅导入模式，退出进程");
            System.exit(0);
        }
    }
}
