package com.gb2760.repository;

import com.gb2760.domain.CategoryNode;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface CategoryRepository extends Neo4jRepository<CategoryNode, String> {

    Optional<CategoryNode> findByCategoryCode(String categoryCode);

    List<CategoryNode> findByCategoryNameContainingIgnoreCaseOrCategoryCodeContaining(
            String categoryName, String categoryCode);
}
