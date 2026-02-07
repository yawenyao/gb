package com.gb2760.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CategoryAdditiveDto {
    private Long faid;
    private String nameCn;
    private String nameEn;
    private String cns;
    private String ins;
    private String function;
    private String maxUsage;
    private String remark;
    private String usageType;
    private String residueNote;
    /** 本级/上级/GMP：direct | parent | gmp */
    private String source;
    /** 单位，如 g/kg、g/L */
    private String unit;
}
