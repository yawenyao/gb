package com.gb2760.service;

import com.gb2760.domain.AdditiveNode;
import com.gb2760.dto.AdditiveDetailDto;
import com.gb2760.dto.UsageItemDto;
import com.gb2760.repository.AdditiveRepository;
import lombok.RequiredArgsConstructor;
import org.neo4j.driver.Driver;
import org.neo4j.driver.Record;
import org.neo4j.driver.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class AdditiveService {

    private final AdditiveRepository additiveRepository;
    private final Driver neo4jDriver;

    public List<AdditiveNode> listAll() {
        return additiveRepository.findAll();
    }

    public Optional<AdditiveDetailDto> getByFaid(Long faid) {
        return additiveRepository.findByFaid(faid)
                .map(a -> {
                    List<UsageItemDto> usages;
                    try (var session = neo4jDriver.session()) {
                        usages = session.run(
                                "MATCH (a:Additive {faid: $faid})-[r:USED_IN]->(c:Category) " +
                                        "RETURN r.foodCategoryCode AS foodCategoryCode, r.foodName AS foodName, " +
                                        "r.maxUsage AS maxUsage, r.remark AS remark, r.usageType AS usageType, r.residueNote AS residueNote",
                                org.neo4j.driver.Values.parameters("faid", faid)
                        ).list().stream().map(this::toUsageItem).collect(Collectors.toList());
                    }
                    return new AdditiveDetailDto(
                            a.getFaid(), a.getNameCn(), a.getNameEn(), a.getCns(), a.getIns(), a.getFunction(),
                            usages
                    );
                });
    }

    private UsageItemDto toUsageItem(Record r) {
        return new UsageItemDto(
                getString(r, "foodCategoryCode"),
                getString(r, "foodName"),
                getString(r, "maxUsage"),
                getString(r, "remark"),
                getString(r, "usageType"),
                getString(r, "residueNote")
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

    public List<AdditiveNode> search(String q) {
        if (q == null || q.isBlank()) return listAll();
        return additiveRepository.findByNameCnContainingIgnoreCaseOrNameEnContainingIgnoreCaseOrCnsContaining(q, q, q);
    }
}
