package com.gb2760.domain;

import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Data
@Node("Category")
@NoArgsConstructor
@AllArgsConstructor
public class CategoryNode {

    @Id
    private String categoryCode;
    private String categoryName;
    private Integer limitId;
}
