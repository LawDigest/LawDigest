package com.everyones.lawmaking.common.dto.response;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyFollowResponse {

    private boolean followChecked;

    public static PartyFollowResponse from(boolean followChecked){
        return PartyFollowResponse.builder()
                .followChecked(followChecked)
                .build();
    }
}


