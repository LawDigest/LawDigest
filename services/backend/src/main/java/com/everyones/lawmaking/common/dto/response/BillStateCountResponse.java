package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.global.constant.BillInfoConstant;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillStateCountResponse {

    @Schema(name = "국회 개원으로부터 경과한 날")
    private final Long daysSinceOpening;
    @Schema(name = "접수 법안")
    private final Long receiptCount;
    @Schema(name = "처리 법안")
    private final Long treatmentCount;
    @Schema(name = "가결 법안")
    private final Long passedCount;

    public BillStateCountResponse(long receiptCount, long treatmentCount, long passedCount) {
        this.daysSinceOpening = BillInfoConstant.getDaysSinceOpening();
        this.receiptCount = receiptCount;
        this.treatmentCount = treatmentCount;
        this.passedCount = passedCount;
    }

}
