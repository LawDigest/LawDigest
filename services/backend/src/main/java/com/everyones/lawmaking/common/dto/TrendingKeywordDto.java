package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class TrendingKeywordDto {

    private String keyword;
    private long count;

    public TrendingKeywordDto(String keyword, long count) {
        this.keyword = keyword;
        this.count = count;
    }
}
