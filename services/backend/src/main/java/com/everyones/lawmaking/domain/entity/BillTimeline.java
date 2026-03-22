package com.everyones.lawmaking.domain.entity;

import com.everyones.lawmaking.common.dto.request.BillStageDfRequest;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;

@Entity
@Data
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillTimeline extends BaseEntity{

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "bill_timeline_id")
    private long id;

    @ManyToOne(fetch=FetchType.LAZY)
    @JoinColumn(name = "bill_id")
    private Bill bill;

    @Column(name = "bill_result")
    String billResult;


    @Column(name="bill_timeline_stage")
    private String billTimelineStage;

    @Column(name = "bill_timeline_committee")
    private String billTimelineCommittee;


    @Column(name = "status_update_date")
    private LocalDate statusUpdateDate;

    public static BillTimeline of (Bill foundBill, BillStageDfRequest billStageDfRequest){
        var stageChangeDate = billStageDfRequest.getStatusUpdateDate();
        return BillTimeline.builder()
                .bill(foundBill)
                .billTimelineCommittee(billStageDfRequest.getCommittee())
                .statusUpdateDate(stageChangeDate)
                .billTimelineStage(billStageDfRequest.getStage())
                .build();
    }


}
