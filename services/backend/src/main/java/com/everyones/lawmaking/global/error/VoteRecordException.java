package com.everyones.lawmaking.global.error;

import java.util.Map;

public class VoteRecordException extends CustomException {
    public VoteRecordException(ErrorCode errorCode) {
        super(errorCode);
    }
    public VoteRecordException(ErrorCode errorCode, Map<String, String> inputValuesByProperty) {
        super(errorCode, inputValuesByProperty);
    }

    public static class VoteRecordNotFound extends VoteRecordException {
        public VoteRecordNotFound() {
            super(ErrorCode.VOTE_RECORD_NOT_FOUND);
        }
        public VoteRecordNotFound(Map<String, String> inputValuesByProperty) {
            super(ErrorCode.VOTE_RECORD_NOT_FOUND, inputValuesByProperty);
        }
    }
}