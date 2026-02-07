package com.gb2760.service;

import com.gb2760.domain.CategoryNode;
import com.gb2760.dto.CategoryAdditiveDto;
import com.gb2760.dto.CategoryDetailDto;
import com.gb2760.repository.CategoryRepository;
import lombok.RequiredArgsConstructor;
import org.neo4j.driver.Driver;
import org.neo4j.driver.Record;
import org.neo4j.driver.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CategoryService {

    private final CategoryRepository categoryRepository;
    private final Driver neo4jDriver;

    public List<CategoryNode> listAll() {
        return categoryRepository.findAll();
    }

    public Optional<CategoryDetailDto> getByCategoryCode(String code) {
        return categoryRepository.findByCategoryCode(code)
                .map(c -> {
                    List<CategoryAdditiveDto> additives;
                    try (var session = neo4jDriver.session()) {
                        additives = session.run(
                                "MATCH (c:Category {categoryCode: $code})<-[r:USED_IN]-(a:Additive) " +
                                        "RETURN a.faid AS faid, a.nameCn AS nameCn, a.nameEn AS nameEn, a.cns AS cns, a.ins AS ins, a.function AS function, " +
                                        "r.maxUsage AS maxUsage, r.remark AS remark, r.usageType AS usageType, r.residueNote AS residueNote, r.source AS source, r.unit AS unit",
                                org.neo4j.driver.Values.parameters("code", code)
                        ).list().stream().map(this::toCategoryAdditive).collect(Collectors.toList());
                    }
                    List<CategoryAdditiveDto> direct = new ArrayList<>();
                    List<CategoryAdditiveDto> parent = new ArrayList<>();
                    List<CategoryAdditiveDto> gmp = new ArrayList<>();
                    for (CategoryAdditiveDto dto : additives) {
                        String src = dto.getSource() != null ? dto.getSource() : "";
                        switch (src) {
                            case "direct": direct.add(dto); break;
                            case "parent": parent.add(dto); break;
                            case "gmp": gmp.add(dto); break;
                            default: direct.add(dto); break;
                        }
                    }
                    return new CategoryDetailDto(c.getCategoryCode(), c.getCategoryName(), c.getLimitId(), additives, direct, parent, gmp);
                });
    }

    private CategoryAdditiveDto toCategoryAdditive(Record r) {
        return new CategoryAdditiveDto(
                getLong(r, "faid"),
                getString(r, "nameCn"),
                getString(r, "nameEn"),
                getString(r, "cns"),
                getString(r, "ins"),
                getString(r, "function"),
                getString(r, "maxUsage"),
                getString(r, "remark"),
                getString(r, "usageType"),
                getString(r, "residueNote"),
                getString(r, "source"),
                getString(r, "unit")
        );
    }

    private static String getString(Record r, String key) {
        try {
            Value v = r.get(key);
            return v == null || v.isNull() ? null : v.asString(null);
        } catch (Exception e) {
            return null;
        }
    }

    private static Long getLong(Record r, String key) {
        try {
            Value v = r.get(key);
            return v == null || v.isNull() ? null : v.asLong(0L);
        } catch (Exception e) {
            return null;
        }
    }

    public List<CategoryNode> search(String q) {
        if (q == null || q.isBlank()) return listAll();
        return categoryRepository.findByCategoryNameContainingIgnoreCaseOrCategoryCodeContaining(q, q);
    }
}
