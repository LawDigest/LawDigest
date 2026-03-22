package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.domain.entity.AuthInfo;
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
public class WithdrawResponse {

    @NotNull
    private String socialId;

    @NotNull
    private String provider;

    public static WithdrawResponse of(AuthInfo authInfo) {
        return WithdrawResponse.builder()
                .socialId(authInfo.getSocialId())
                .provider(authInfo.getProvider().name())
                .build();
    }

}
