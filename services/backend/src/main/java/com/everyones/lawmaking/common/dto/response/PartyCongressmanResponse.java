package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.common.dto.PartyCongressmanDto;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@AllArgsConstructor
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyCongressmanResponse {

    @NotNull
    private List<PartyCongressmanDto> partyCongressman;

    public static PartyCongressmanResponse of(List<PartyCongressmanDto> partyCongressmanList) {
        return PartyCongressmanResponse.builder()
                .partyCongressman(partyCongressmanList)
                .build();
    }
}
