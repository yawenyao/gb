package com.gb2760.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class UsageItemDto {
    private String foodCategoryCode;
    private String foodName;
    private String maxUsage;
    private String remark;
    private String usageType;
    private String residueNote;
}
