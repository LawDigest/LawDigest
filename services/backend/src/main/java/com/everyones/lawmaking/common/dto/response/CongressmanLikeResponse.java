package com.everyones.lawmaking.common.dto.response;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@AllArgsConstructor
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CongressmanLikeResponse {

    @NotNull
    private boolean likeChecked;

    public static CongressmanLikeResponse from(boolean likeChecked){
        return CongressmanLikeResponse.builder()
                .likeChecked(likeChecked)
                .build();
    }

}
