package com.everyones.lawmaking.domain.entity;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@Getter
public enum ProposerKindType {

    CONGRESSMAN("의원"),
    CHAIRMAN("위원장");

    private final String proposerKind;

    public static ProposerKindType from(String stringValue) {
        if (stringValue == null) {
            throw new IllegalArgumentException("Proposer kind type cannot be null.");
        }

        for (ProposerKindType proposerKindType : ProposerKindType.values()) {
            if (proposerKindType.getProposerKind().equals(stringValue)) {
                return proposerKindType;
            }
        }
        throw new IllegalArgumentException("Unknown proposer kind type: " + stringValue);

    }


}
