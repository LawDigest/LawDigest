package com.everyones.lawmaking.common.dto.response;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.Getter;

@Builder
@Getter
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillTimelinePaginationResponse {

    PaginationResponse paginationResponse;

    List<BillTimelineResponse> timelineResponseList;

    public static BillTimelinePaginationResponse of(PaginationResponse paginationResponse, List<BillTimelineResponse> timelineResponseList) {
        return BillTimelinePaginationResponse.builder()
                .paginationResponse(paginationResponse)
                .timelineResponseList(timelineResponseList)
                .build();
    }
}
