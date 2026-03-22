package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.BillProposer;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.querydsl.core.annotations.QueryProjection;
import lombok.Builder;
import lombok.Getter;

@Builder
@Getter
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PublicProposerDto {
    private String publicProposerId;
    private String publicProposerName;
    private String publicProposerImgUrl;

    private long publicProposerPartyId;
    private String publicProposerPartyName;
    private String publicProposerPartyImageUrl;

    @QueryProjection
    public PublicProposerDto(
            String publicProposerId,
            String publicProposerName,
            String publicProposerImgUrl,
            long publicProposerPartyId,
            String publicProposerPartyName,
            String publicProposerPartyImageUrl
    ) {
        this.publicProposerId = publicProposerId;
        this.publicProposerName = publicProposerName;
        this.publicProposerImgUrl = publicProposerImgUrl;
        this.publicProposerPartyId = publicProposerPartyId;
        this.publicProposerPartyName= publicProposerPartyName;
        this.publicProposerPartyImageUrl = publicProposerPartyImageUrl;
    }

    public static PublicProposerDto from(BillProposer billProposer) {
        var congressman = billProposer.getCongressman();
        var party = billProposer.getParty();
        return PublicProposerDto.builder()
                .publicProposerId(congressman.getId())
                .publicProposerName(congressman.getName())
                .publicProposerImgUrl(congressman.getCongressmanImageUrl())
                .publicProposerPartyId(party.getId())
                .publicProposerPartyName(party.getName())
                .publicProposerPartyImageUrl(party.getPartyImageUrl())
                .build();
    }
}
