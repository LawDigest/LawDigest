package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CommitteeAuditDto {

    private String committeeName;

    private Integer billCount;

    private List<BillOutlineDto> billOutlineDtoList;

    public static CommitteeAuditDto of(String committeeName, List<BillOutlineDto> billOutlineDtoList) {
        return CommitteeAuditDto.builder()
                .committeeName(committeeName)
                .billCount(billOutlineDtoList.size())
                .billOutlineDtoList(billOutlineDtoList)
                .build();
    }
}
