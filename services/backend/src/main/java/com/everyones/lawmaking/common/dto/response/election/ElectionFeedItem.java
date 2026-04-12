package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionFeedItem {

    private String id;
    private String type;
    private String publishedAt;
    private Object payload;

    public static ElectionFeedItem of(String id, String type, String publishedAt, Object payload) {
        return ElectionFeedItem.builder()
                .id(id)
                .type(type)
                .publishedAt(publishedAt)
                .payload(payload)
                .build();
    }
}
