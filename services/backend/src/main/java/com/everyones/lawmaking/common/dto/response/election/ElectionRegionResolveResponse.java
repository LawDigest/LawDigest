package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionRegionResolveResponse {

    private String electionId;
    private String state; // idle, requesting-permission, manual-required, gps-suggested, confirmed
    private boolean confirmationRequired;
    private String suggestedRegionType;
    private String suggestedRegionCode;
    private String suggestedRegionName;
    private boolean manualCorrectionAvailable;
    private boolean denyAvailable;
}
