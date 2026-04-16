package com.everyones.lawmaking.domain.entity;

import com.everyones.lawmaking.common.dto.request.BillDfRequest;
import com.everyones.lawmaking.common.dto.request.BillStageDfRequest;
import com.everyones.lawmaking.global.constant.BillStageType;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.*;
import org.hibernate.annotations.ColumnDefault;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;


@Entity
@Data
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
@Table(name = "Bill", indexes = {
        @Index(name = "idx_bill_id_propose_date", columnList = "propose_date DESC"),
        @Index(name = "idx_propose_date_id", columnList = "propose_date, bill_id"),
        @Index(name = "idx_bill_ingest_status_propose_date_id", columnList = "ingest_status, propose_date, bill_id")
})public class Bill extends BaseEntity{
    @Id
    @Column(name = "bill_id")
    private String id;

    @Column(name = "bill_number", unique = true)
    private int billNumber;

    @NotNull
    @Column(name = "assembly_number")
    private int assemblyNumber;

    @Column(name = "bill_name")
    private String billName;

    @Column(name = "proposers")
    private String proposers;

    @ToString.Exclude
    @OneToMany(mappedBy = "bill")
    private List<BillProposer> publicProposer;

    @ToString.Exclude
    @OneToMany(mappedBy = "bill", fetch = FetchType.LAZY)
    private List<RepresentativeProposer> representativeProposer;

    @ToString.Exclude
    @OneToMany(mappedBy = "bill")
    private List<BillLike> billLike;

    @ToString.Exclude
    @OneToMany(mappedBy = "bill")
    private List<VoteParty> votePartyList;



    private String committee;

    @Column(name = "propose_date")
    private LocalDate proposeDate;

    @Column(name = "stage")
    private String stage;

    @Column(name = "bill_result")
    private String billResult;

    @Column(name = "proposer_kind")
    @ColumnDefault("'CONGRESSMAN'")
    @Enumerated(EnumType.STRING)
    private ProposerKindType proposerKind;

    @Column(name = "ingest_status")
    @ColumnDefault("'PENDING'")
    @Enumerated(EnumType.STRING)
    private IngestStatusType ingestStatus;

    @Column(columnDefinition = "TEXT")
    private String summary;

    @Column(name = "gpt_summary", columnDefinition = "TEXT")
    private String gptSummary;


    @Column(name = "bill_pdf_url")
    private String billPdfUrl; // PDF 파일의 경로 또는 식별자

    @Column(name = "brief_summary", columnDefinition = "TEXT")
    private String briefSummary;

    @Column(name ="bill_link")
    private String billLink;

    @ColumnDefault("0")
    private int viewCount;

    @ToString.Exclude
    @OneToMany(mappedBy = "bill")
    private List<BillTimeline> billTimelineList = new ArrayList<>();

    public static Bill of(BillDfRequest billDfRequest){
        return Bill.builder()
                .id(billDfRequest.getBillId())
                .billResult(billDfRequest.getBillResult())
                .billNumber(billDfRequest.getBillNumber())
                .billName(billDfRequest.getBillName())
                .proposeDate(billDfRequest.getProposeDate())
                .proposers(billDfRequest.getProposers())
                .assemblyNumber(billDfRequest.getAssemblyNumber())
                .stage(billDfRequest.getStage())
                .gptSummary(billDfRequest.getGptSummary())
                .summary(billDfRequest.getSummary())
                .briefSummary(billDfRequest.getBriefSummary())
                .proposerKind(ProposerKindType.from(billDfRequest.getProposerKind()))
                .ingestStatus(resolveIngestStatus(
                        billDfRequest.getBillName(),
                        billDfRequest.getProposeDate(),
                        billDfRequest.getStage(),
                        billDfRequest.getSummary()
                ))
                .build();
    }

    public void updateContent(BillDfRequest billDfRequest){
        this.setBillResult(billDfRequest.getBillResult());
        this.setBillNumber(billDfRequest.getBillNumber());
        this.setBillName(billDfRequest.getBillName());
        this.setProposeDate(billDfRequest.getProposeDate());
        this.setProposers(billDfRequest.getProposers());
        this.setAssemblyNumber(billDfRequest.getAssemblyNumber());
        this.setStage(billDfRequest.getStage());
        this.setGptSummary(billDfRequest.getGptSummary());
        this.setSummary(billDfRequest.getSummary());
        this.setBriefSummary(billDfRequest.getBriefSummary());
        this.setProposerKind(ProposerKindType.from(billDfRequest.getProposerKind()));
        this.setIngestStatus(resolveIngestStatus(
                billDfRequest.getBillName(),
                billDfRequest.getProposeDate(),
                billDfRequest.getStage(),
                billDfRequest.getSummary()
        ));

    }

    public void updateStatusByStep(BillStageDfRequest billStageDfRequest){
        BillStageType currentStage = BillStageType.fromValue(this.stage);
        BillStageType nextStage = BillStageType.fromValue(billStageDfRequest.getStage());

        // 단계의 order가 커야 수정 가능 (심의 단계가 다음 단계일 때만 수정이 가능.)
        if (BillStageType.canUpdateStage(currentStage, nextStage)) {
            this.setStage(billStageDfRequest.getStage());
            this.setCommittee(billStageDfRequest.getCommittee());
        }
    }

    private static IngestStatusType resolveIngestStatus(
            String billName,
            LocalDate proposeDate,
            String stage,
            String summary
    ) {
        if (hasText(billName) && proposeDate != null && hasText(stage) && hasText(summary)) {
            return IngestStatusType.READY;
        }

        if (hasText(billName) || proposeDate != null || hasText(stage) || hasText(summary)) {
            return IngestStatusType.PARTIAL;
        }

        return IngestStatusType.PENDING;
    }

    private static boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

}
