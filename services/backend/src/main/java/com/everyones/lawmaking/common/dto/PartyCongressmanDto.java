package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.Congressman;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Builder
@Getter
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyCongressmanDto {

    @NotNull
    private String congressmanId;

    @NotNull
    private String congressmanName;

    @NotNull
    private String congressmanImageUrl;

    public static PartyCongressmanDto from(Congressman congressman) {
        return PartyCongressmanDto.builder()
                .congressmanId(congressman.getId())
                .congressmanName(congressman.getName())
                .congressmanImageUrl(congressman.getCongressmanImageUrl())
                .build();
    }

}
