package com.gb2760.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AdditiveDetailDto {
    private Long faid;
    private String nameCn;
    private String nameEn;
    private String cns;
    private String ins;
    private String function;
    private List<UsageItemDto> usage;
}
