package com.everyones.lawmaking.common.dto.response.election.feed;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ScheduleFeedPayload {

    private String title;
    private String description;
    private String eventDate;
    private String eventType;

    public static ScheduleFeedPayload of(String title, String description, String eventDate, String eventType) {
        return ScheduleFeedPayload.builder()
                .title(title)
                .description(description)
                .eventDate(eventDate)
                .eventType(eventType)
                .build();
    }
}
