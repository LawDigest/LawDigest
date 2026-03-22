package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.domain.entity.Bill;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@AllArgsConstructor
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillViewCountResponse {
    private String billId;

    private int viewCount;


    public static BillViewCountResponse from(Bill bill) {
        return BillViewCountResponse.builder()
                .billId(bill.getId())
                .viewCount(bill.getViewCount())
                .build();

    }
}
