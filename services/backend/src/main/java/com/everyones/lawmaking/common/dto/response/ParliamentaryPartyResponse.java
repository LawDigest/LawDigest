package com.everyones.lawmaking.common.dto.response;


import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ParliamentaryPartyResponse {
    private long partyId;
    private String partyName;
    private String partyImageUrl;
    private Long congressmanCount;

    public ParliamentaryPartyResponse(long partyId, String partyName, String partyImageUrl, Long congressmanCount) {
        this.partyId = partyId;
        this.partyName = partyName;
        this.partyImageUrl = partyImageUrl;
        this.congressmanCount = congressmanCount;
    }

    /** 제22대 의석수 = 지역구 + 비례대표 의석 (Party 엔티티의 사전 집계 컬럼 기반). */
    public ParliamentaryPartyResponse(long partyId, String partyName, String partyImageUrl,
                                      int districtCongressmanCount, int proportionalCongressmanCount) {
        this.partyId = partyId;
        this.partyName = partyName;
        this.partyImageUrl = partyImageUrl;
        this.congressmanCount = (long) (districtCongressmanCount + proportionalCongressmanCount);
    }
}
