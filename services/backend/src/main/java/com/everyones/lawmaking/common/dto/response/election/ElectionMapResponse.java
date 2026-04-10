package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionMapResponse {

    private String selectedElectionId;
    private Integer depth;
    private String regionCode;
    private String viewMode;
    private List<RegionItem> regions;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class RegionItem {
        private String regionCode;
        private String regionName;
        private Integer value; // 후보자 수 등
    }
}
