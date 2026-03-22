package com.everyones.lawmaking.common.dto.projection;

import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;


@Getter
@NoArgsConstructor
@Builder
public class CommitteeBillDto {
    private String committeeName;
    private List<String> billIds;

    public CommitteeBillDto(String committeeName, List<String> billIds) {
        this.committeeName = committeeName;
        this.billIds = billIds;
    }
    public static CommitteeBillDto of(String committeeName, List<String> billIds) {
        return CommitteeBillDto.builder()
                .committeeName(committeeName)
                .billIds(billIds)
                .build();
    }
}
