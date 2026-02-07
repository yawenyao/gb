package com.gb2760.controller;

import com.gb2760.domain.AdditiveNode;
import com.gb2760.dto.AdditiveDetailDto;
import com.gb2760.service.AdditiveService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/additives")
@RequiredArgsConstructor
@CrossOrigin
public class AdditiveController {

    private final AdditiveService additiveService;

    @GetMapping
    public List<AdditiveNode> list(@RequestParam(required = false) String q) {
        return additiveService.search(q);
    }

    @GetMapping("/{faid}")
    public ResponseEntity<AdditiveDetailDto> get(@PathVariable Long faid) {
        return additiveService.getByFaid(faid)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
