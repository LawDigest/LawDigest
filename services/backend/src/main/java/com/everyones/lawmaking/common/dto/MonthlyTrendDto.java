package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 월별 발의 추이 한 점. month는 'YYYY-MM'. */
@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class MonthlyTrendDto {

    private String month;
    private long count;

    public MonthlyTrendDto(String month, long count) {
        this.month = month;
        this.count = count;
    }
}
