package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.Bill;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@AllArgsConstructor
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillDetailInfo extends BillInfoDto{

    private String billLink;
    private String billResult;


    public BillDetailInfo(Bill bill) {
        super(bill);
        this.billLink = bill.getBillLink();
        this.billResult = bill.getBillResult();
    }

    public static BillDetailInfo from(Bill bill) {
        return new BillDetailInfo(bill);
    }

}

