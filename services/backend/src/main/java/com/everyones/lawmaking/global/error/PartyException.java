package com.everyones.lawmaking.global.error;

import java.util.Map;

public class PartyException extends CustomException {

    public PartyException(final ErrorCode errorCode) {
        super(errorCode);
    }
    public PartyException(final ErrorCode errorCode, final Map<String, String> inputValuesByProperty) {
        super(errorCode, inputValuesByProperty);
    }

    public static class PartyNotFound extends PartyException {
        public PartyNotFound() {
            super(ErrorCode.PARTY_NOT_FOUND);
        }
        public PartyNotFound(Map<String, String> inputValuesByProperty) {
            super(ErrorCode.PARTY_NOT_FOUND, inputValuesByProperty);
        }
    }
}
