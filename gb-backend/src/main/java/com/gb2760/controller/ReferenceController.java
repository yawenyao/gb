package com.gb2760.controller;

import com.gb2760.service.ReferenceDataService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/reference")
@RequiredArgsConstructor
@CrossOrigin
public class ReferenceController {

    private final ReferenceDataService referenceDataService;

    @GetMapping("/processing-aids")
    public List<Map<String, Object>> processingAids() {
        return referenceDataService.getProcessingAids();
    }

    @GetMapping("/enzymes")
    public List<Map<String, Object>> enzymes() {
        return referenceDataService.getEnzymes();
    }

    @GetMapping("/spices/b1")
    public List<Map<String, Object>> spicesB1() {
        return referenceDataService.getSpicesB1();
    }

    @GetMapping("/spices/b2")
    public List<Map<String, Object>> spicesB2() {
        return referenceDataService.getSpicesB2();
    }

    @GetMapping("/spices/b3")
    public List<Map<String, Object>> spicesB3() {
        return referenceDataService.getSpicesB3();
    }

    @GetMapping("/appendix-d")
    public List<Map<String, Object>> appendixD() {
        return referenceDataService.getAppendixDFunctions();
    }

    @GetMapping("/site-rules")
    public ResponseEntity<Map<String, Object>> siteRules() {
        Map<String, Object> rules = referenceDataService.getSiteRules();
        return rules.isEmpty() ? ResponseEntity.notFound().build() : ResponseEntity.ok(rules);
    }

    @GetMapping("/spices-rules")
    public ResponseEntity<Map<String, Object>> spicesRules() {
        Map<String, Object> rules = referenceDataService.getSpicesRulesPrinciples();
        return rules.isEmpty() ? ResponseEntity.notFound().build() : ResponseEntity.ok(rules);
    }
}
