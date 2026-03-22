package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.domain.entity.SearchKeyword;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

@Data
@AllArgsConstructor
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class SearchKeywordResponse {

    private String searchWord;

    public static SearchKeywordResponse from(SearchKeyword searchKeyword) {
        return SearchKeywordResponse.builder()
                .searchWord(searchKeyword.getSearchWord())
                .build();

    }
}
