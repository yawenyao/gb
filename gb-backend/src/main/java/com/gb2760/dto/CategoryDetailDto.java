package com.gb2760.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CategoryDetailDto {
    private String categoryCode;
    private String categoryName;
    private Integer limitId;
    /** 该分类下全部添加剂（扁平列表） */
    private List<CategoryAdditiveDto> additives;
    /** 按「本级/上级/GMP」分组，便于前端直接展示三张表 */
    private List<CategoryAdditiveDto> directAdditives;
    private List<CategoryAdditiveDto> parentAdditives;
    private List<CategoryAdditiveDto> gmpAdditives;
}
