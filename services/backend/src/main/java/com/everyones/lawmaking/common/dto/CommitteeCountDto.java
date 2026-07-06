package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 위원회별 법안 수(가결 수 포함). */
@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CommitteeCountDto {

    private String committee;
    private long count;
    private long passedCount;

    public CommitteeCountDto(String committee, Long count, Long passedCount) {
        this.committee = committee;
        this.count = count == null ? 0L : count;
        this.passedCount = passedCount == null ? 0L : passedCount;
    }
}
