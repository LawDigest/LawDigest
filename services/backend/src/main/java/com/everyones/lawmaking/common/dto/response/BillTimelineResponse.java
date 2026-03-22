package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.common.dto.BillOutlineDto;
import com.everyones.lawmaking.common.dto.CommitteeAuditDto;
import com.everyones.lawmaking.common.dto.PlenaryDto;
import com.everyones.lawmaking.common.dto.PromulgationDto;
import com.everyones.lawmaking.domain.entity.BillTimeline;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDate;
import java.util.List;

@Getter
@Builder
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillTimelineResponse {

    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
    LocalDate date;

    Integer billCount;

    @Schema(name = "접수된 법안")
    List<BillOutlineDto> submittedList;

    @Schema(name = "본회의 심의")
    List<PlenaryDto> plenaryList;

    @Schema(name = "법안 공포")
    List<BillOutlineDto> promulgationList;

    @Schema(name = "위원회 심사 법안 목록 리스트")
    List<CommitteeAuditDto> committeeAuditList;

    public static BillTimelineResponse of(LocalDate date, List<BillOutlineDto> submittedList,List<PlenaryDto> plenaryList, List<BillOutlineDto> promulgationList, List<CommitteeAuditDto> committeeAuditList) {
        return BillTimelineResponse.builder()
                .date(date)
                .billCount(submittedList.size() +plenaryList.size() + promulgationList.size() + committeeAuditList.size())
                .submittedList(submittedList)
                .plenaryList(plenaryList)
                .promulgationList(promulgationList)
                .committeeAuditList(committeeAuditList)
                .build();

    }


}
