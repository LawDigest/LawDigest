package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionFeedResponse {

    private List<ElectionFeedItem> items;
    private String nextCursor;
    private boolean hasMore;

    public static ElectionFeedResponse of(List<ElectionFeedItem> items, String nextCursor, boolean hasMore) {
        return ElectionFeedResponse.builder()
                .items(items)
                .nextCursor(nextCursor)
                .hasMore(hasMore)
                .build();
    }
}
