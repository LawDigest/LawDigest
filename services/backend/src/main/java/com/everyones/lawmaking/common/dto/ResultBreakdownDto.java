package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 처리 결과(bill_result)별 분포. 결과 미정(NULL)은 '계류'로 내려준다. */
@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ResultBreakdownDto {

    private String result;
    private long count;

    public ResultBreakdownDto(String result, Long count) {
        this.result = result == null ? "계류" : result;
        this.count = count == null ? 0L : count;
    }
}
