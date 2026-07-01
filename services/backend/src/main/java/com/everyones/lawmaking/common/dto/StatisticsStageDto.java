package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 입법 진행 단계 퍼널(누적). 접수 → 위원회 심사 → 본회의 심의 → 공포 순으로 도달 건수. */
@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class StatisticsStageDto {

    private long receiptCount; // 접수(전체)
    private long committeeCount; // 위원회 심사 이상 도달
    private long plenaryCount; // 본회의 심의 이상 도달
    private long promulgatedCount; // 공포

    public StatisticsStageDto(Long receiptCount, Long committeeCount, Long plenaryCount, Long promulgatedCount) {
        this.receiptCount = receiptCount == null ? 0L : receiptCount;
        this.committeeCount = committeeCount == null ? 0L : committeeCount;
        this.plenaryCount = plenaryCount == null ? 0L : plenaryCount;
        this.promulgatedCount = promulgatedCount == null ? 0L : promulgatedCount;
    }
}
