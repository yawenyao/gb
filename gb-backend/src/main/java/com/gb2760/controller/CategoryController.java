package com.gb2760.controller;

import com.gb2760.domain.CategoryNode;
import com.gb2760.dto.CategoryDetailDto;
import com.gb2760.service.CategoryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/categories")
@RequiredArgsConstructor
@CrossOrigin
public class CategoryController {

    private final CategoryService categoryService;

    @GetMapping
    public List<CategoryNode> list(@RequestParam(required = false) String q) {
        return categoryService.search(q);
    }

    @GetMapping("/{code}")
    public ResponseEntity<CategoryDetailDto> get(@PathVariable String code) {
        return categoryService.getByCategoryCode(code)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
