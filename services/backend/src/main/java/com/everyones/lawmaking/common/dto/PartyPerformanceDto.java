package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 정당별 대표발의·가결 실적. passRate는 %(소수 1자리). */
@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyPerformanceDto {

    private long partyId;
    private String partyName;
    private long count;
    private long passedCount;
    private double passRate;

    public PartyPerformanceDto(Long partyId, String partyName, Long count, Long passedCount) {
        this.partyId = partyId == null ? 0L : partyId;
        this.partyName = partyName;
        this.count = count == null ? 0L : count;
        this.passedCount = passedCount == null ? 0L : passedCount;
        this.passRate = this.count == 0 ? 0.0
                : Math.round(this.passedCount * 1000.0 / this.count) / 10.0;
    }
}
