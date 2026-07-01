package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.common.dto.CongressmanRankingDto;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

import java.util.List;

@Builder
@Data
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CongressmanListResponse {
    private PaginationResponse paginationResponse;

    private List<CongressmanRankingDto> congressmanList;

    public static CongressmanListResponse of(PaginationResponse paginationResponse, List<CongressmanRankingDto> congressmanList) {
        return CongressmanListResponse.builder()
                .paginationResponse(paginationResponse)
                .congressmanList(congressmanList)
                .build();
    }
}
