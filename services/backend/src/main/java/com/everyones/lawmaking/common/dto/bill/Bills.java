package com.everyones.lawmaking.common.dto.bill;

import java.util.List;
import lombok.Getter;

/**
 * BillList의 일급 컬렉션
 * @author 강정훈
 */
@Getter
public class Bills {
    private final List<BillDto> billList;

    public Bills(List<BillDto> billList) {
        this.billList = billList;
    }

}
