package com.everyones.lawmaking.common.dto.response;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@AllArgsConstructor
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class NotificationCountResponse {
    private Long userId;

    private int notificationCount;


    public static NotificationCountResponse of(Long userId, Integer notificationCount) {
        return NotificationCountResponse.builder()
                .userId(userId)
                .notificationCount(notificationCount)
                .build();

    }
}
