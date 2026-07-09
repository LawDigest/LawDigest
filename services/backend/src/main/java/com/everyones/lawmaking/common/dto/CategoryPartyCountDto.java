package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 분야×정당 교차 집계 한 셀. */
@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CategoryPartyCountDto {

    private String category;
    private long partyId;
    private String partyName;
    private long count;

    public CategoryPartyCountDto(String category, Long partyId, String partyName, Long count) {
        this.category = category;
        this.partyId = partyId == null ? 0L : partyId;
        this.partyName = partyName;
        this.count = count == null ? 0L : count;
    }
}
