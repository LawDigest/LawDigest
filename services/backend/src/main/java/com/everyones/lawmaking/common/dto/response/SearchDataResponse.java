package com.everyones.lawmaking.common.dto.response;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
@Builder
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class SearchDataResponse {

    private List<SearchResponse> searchResponse;


    public SearchDataResponse of(List<SearchResponse> searchResponse) {
        return SearchDataResponse.builder()
                .searchResponse(searchResponse)
                .build();
    }

}
