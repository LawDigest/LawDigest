package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 월별 발의·가결 추이 한 점. month는 'YYYY-MM', passedCount는 해당 월 발의분 중 가결된 수. */
@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class MonthlyTrendDetailDto {

    private String month;
    private long proposedCount;
    private long passedCount;

    public MonthlyTrendDetailDto(String month, long proposedCount, long passedCount) {
        this.month = month;
        this.proposedCount = proposedCount;
        this.passedCount = passedCount;
    }
}
