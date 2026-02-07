package com.gb2760.domain;

import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.Relationship;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Data
@Node("Additive")
@NoArgsConstructor
@AllArgsConstructor
public class AdditiveNode {

    @Id
    private Long faid;
    private String nameCn;
    private String nameEn;
    private String cns;
    private String ins;
    private String function;

    @Relationship(type = "USED_IN", direction = Relationship.Direction.OUTGOING)
    private List<UsedInRelation> usages = new ArrayList<>();
}
