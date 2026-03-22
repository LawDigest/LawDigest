package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.domain.entity.User;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class UserMyPageInfoResponse {

    @NotNull
    private long userId;

    @NotNull
    private String userName;

    @NotNull
    private String userImageUrl;

    @NotNull
    private String userEmail;

    public static UserMyPageInfoResponse from(User user) {
        return UserMyPageInfoResponse.builder()
                .userId(user.getId())
                .userName(user.getName())
                .userEmail(user.getEmail())
                .userImageUrl(user.getImageUrl())
                .build();
    }
}
