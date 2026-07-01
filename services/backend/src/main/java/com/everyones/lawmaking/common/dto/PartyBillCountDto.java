package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 정당별 대표발의 법안 수. */
@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyBillCountDto {

    private long partyId;
    private String partyName;
    private long count;

    public PartyBillCountDto(Long partyId, String partyName, Long count) {
        this.partyId = partyId == null ? 0L : partyId;
        this.partyName = partyName;
        this.count = count == null ? 0L : count;
    }
}
