package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class StatisticsOverviewDto {

    private long totalCount; // 총 발의
    private long passedCount; // 가결(원안가결 + 수정가결)
    private long pendingCount; // 계류(결과 미정)
    private double passRate; // 가결률(%)

    public StatisticsOverviewDto(Long totalCount, Long passedCount, Long pendingCount) {
        this.totalCount = totalCount == null ? 0L : totalCount;
        this.passedCount = passedCount == null ? 0L : passedCount;
        this.pendingCount = pendingCount == null ? 0L : pendingCount;
        this.passRate = this.totalCount == 0 ? 0.0
                : Math.round(this.passedCount * 1000.0 / this.totalCount) / 10.0;
    }
}
