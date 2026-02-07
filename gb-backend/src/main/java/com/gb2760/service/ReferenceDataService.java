package com.gb2760.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class ReferenceDataService {

    private final ResourceLoader resourceLoader;
    private final ObjectMapper objectMapper;

    @Value("${dataset.path:}")
    private String datasetPath;

    private Path basePath;

    @PostConstruct
    public void init() {
        if (datasetPath != null && !datasetPath.isBlank()) {
            basePath = Path.of(datasetPath);
            if (!Files.isDirectory(basePath)) {
                basePath = null;
            }
        }
    }

    public List<Map<String, Object>> getProcessingAids() {
        return readJsonList("reference/processing_aids.json");
    }

    public List<Map<String, Object>> getEnzymes() {
        return readJsonList("reference/enzymes.json");
    }

    public List<Map<String, Object>> getSpicesB1() {
        return readJsonList("reference/spices_b1_prohibited.json");
    }

    public List<Map<String, Object>> getSpicesB2() {
        return readJsonList("reference/spices_b2_natural.json");
    }

    public List<Map<String, Object>> getSpicesB3() {
        return readJsonList("reference/spices_b3_synthetic.json");
    }

    public List<Map<String, Object>> getAppendixDFunctions() {
        return readJsonList("reference/appendix_d_functions.json");
    }

    public Map<String, Object> getSiteRules() {
        return readJsonMap("reference/site_rules.json");
    }

    public Map<String, Object> getSpicesRulesPrinciples() {
        return readJsonMap("reference/spices_rules_principles.json");
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> readJsonList(String relative) {
        if (basePath == null) return Collections.emptyList();
        try {
            Path p = basePath.resolve(relative);
            if (!Files.exists(p)) return Collections.emptyList();
            List<?> list = objectMapper.readValue(Files.newInputStream(p), List.class);
            return (List<Map<String, Object>>) list;
        } catch (IOException e) {
            return Collections.emptyList();
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> readJsonMap(String relative) {
        if (basePath == null) return Collections.emptyMap();
        try {
            Path p = basePath.resolve(relative);
            if (!Files.exists(p)) return Collections.emptyMap();
            return objectMapper.readValue(Files.newInputStream(p), Map.class);
        } catch (IOException e) {
            return Collections.emptyMap();
        }
    }
}
