package com.gb2760.domain;

import org.springframework.data.neo4j.core.schema.GeneratedValue;
import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.RelationshipProperties;
import org.springframework.data.neo4j.core.schema.TargetNode;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Data
@RelationshipProperties
@NoArgsConstructor
@AllArgsConstructor
public class UsedInRelation {

    @Id
    @GeneratedValue
    private Long id;

    private String foodCategoryCode;
    private String foodName;
    private String maxUsage;
    private String remark;
    private String usageType;
    private String residueNote;
    /** 本级/上级/GMP：direct | parent | gmp，用于按「本级/上级/GMP」分组展示 */
    private String source;
    /** 从 maxUsage 提取的单位，如 g/kg、g/L，便于展示与筛选 */
    private String unit;

    @TargetNode
    private CategoryNode category;
}
