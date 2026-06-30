package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.querydsl.core.annotations.QueryProjection;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CategoryCountDto {

    private String category;
    private long count;

    @QueryProjection
    public CategoryCountDto(String category, Long count) {
        this.category = category;
        this.count = count == null ? 0L : count;
    }
}
