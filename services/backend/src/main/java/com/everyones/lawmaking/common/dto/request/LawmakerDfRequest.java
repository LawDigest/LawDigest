package com.everyones.lawmaking.common.dto.request;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@AllArgsConstructor
@NoArgsConstructor
public class LawmakerDfRequest {

    private boolean isInsert;
    private String congressmanId;
    private String congressmanName;
    private String congressmanImageUrl;
    private String commits;
    private String partyName;
    private String elected;
    private String homepage;
    private String district;
    private String congressmanBirth;
    private String sex;
    private String email;
    private String congressmanOffice;
    private String congressmanTelephone;
    private String briefHistory;
    private int assemblyNumber;

}
