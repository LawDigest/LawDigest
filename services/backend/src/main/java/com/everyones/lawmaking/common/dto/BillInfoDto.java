package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.Bill;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.querydsl.core.annotations.QueryProjection;
import java.time.LocalDate;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Builder
@Getter
@AllArgsConstructor
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillInfoDto {

    private String billId;
    private String billName;
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd", timezone = "Asia/Seoul")
    private LocalDate proposeDate;
    private String summary;
    private String gptSummary;
    private int viewCount;
    private int billLikeCount;
    private String billStage;
    private String briefSummary;

    @QueryProjection
    public BillInfoDto(Bill bill) {
        this.billId = bill.getId();
        this.billName = bill.getBillName();
        this.proposeDate = bill.getProposeDate();
        this.summary = bill.getSummary();
        this.gptSummary = bill.getGptSummary();
        this.viewCount = bill.getViewCount();
        this.billLikeCount = bill.getBillLike().size();
        this.billStage = bill.getStage();
        this.briefSummary = bill.getBriefSummary();
    }
    @Deprecated
    public static BillInfoDto from(Bill bill) {
        var billLikeCount = bill.getBillLike().size();
        return BillInfoDto.builder()
                .billId(bill.getId())
                .billName(bill.getBillName())
                .proposeDate(bill.getProposeDate())
                .summary(bill.getSummary())
                .gptSummary(bill.getGptSummary())
                .viewCount(bill.getViewCount())
                .billLikeCount(billLikeCount)
                .billStage(bill.getStage())
                .briefSummary(bill.getBriefSummary())
                .build();
    }

}
