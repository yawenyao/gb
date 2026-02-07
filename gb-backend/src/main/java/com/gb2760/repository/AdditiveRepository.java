package com.gb2760.repository;

import com.gb2760.domain.AdditiveNode;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface AdditiveRepository extends Neo4jRepository<AdditiveNode, Long> {

    Optional<AdditiveNode> findByFaid(Long faid);

    List<AdditiveNode> findByNameCnContainingIgnoreCaseOrNameEnContainingIgnoreCaseOrCnsContaining(
            String nameCn, String nameEn, String cns);

    @Query("MATCH (a:Additive)-[r:USED_IN]->(c:Category) WHERE a.faid = $faid RETURN a, collect(r), collect(c)")
    Optional<AdditiveNode> findWithUsagesByFaid(@Param("faid") Long faid);

    @Query("MATCH (c:Category {categoryCode: $code})<-[r:USED_IN]-(a:Additive) RETURN a, collect(r), collect(c) ORDER BY a.nameCn")
    List<AdditiveNode> findAdditivesByCategoryCode(@Param("code") String code);
}
