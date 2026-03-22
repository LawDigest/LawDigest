package com.everyones.lawmaking.common.dto.bill;


import com.everyones.lawmaking.common.dto.BillInfoDto;
import com.everyones.lawmaking.common.dto.PublicProposerDto;
import com.everyones.lawmaking.common.dto.proposer.RepresentativeProposerDto;
import com.everyones.lawmaking.domain.entity.Bill;
import com.everyones.lawmaking.domain.entity.BillProposer;
import com.everyones.lawmaking.domain.entity.RepresentativeProposer;
import com.fasterxml.jackson.annotation.Nulls;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;


@Builder
@Data
@AllArgsConstructor
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillDto {

    @NotNull
    private BillInfoDto billInfoDto;

    @NotNull
    private List<RepresentativeProposerDto> representativeProposerDtoList;

    @NotNull
    private List<PublicProposerDto> publicProposerDtoList;

    @NotNull
    private Boolean isBookMark;

    public static BillDto of(BillInfoDto billInfoDto, List<RepresentativeProposerDto> representativeProposerList, List<PublicProposerDto> publicProposerDtoList, boolean isBookMark) {
        return BillDto.builder()
                .billInfoDto(billInfoDto)
                .representativeProposerDtoList(representativeProposerList)
                .publicProposerDtoList(publicProposerDtoList)
                .isBookMark(isBookMark)
                .build();
    }

}
