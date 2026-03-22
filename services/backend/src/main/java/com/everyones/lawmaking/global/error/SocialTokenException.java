package com.everyones.lawmaking.global.error;

import java.util.Map;

public class SocialTokenException extends CustomException {
    public SocialTokenException(ErrorCode errorCode) {
        super(errorCode);
    }
    public SocialTokenException(ErrorCode errorCode, Map<String, String> inputValueProperties) {
        super(errorCode, inputValueProperties);
    }

    public static class SocialTokenNotFound extends NotificationException {

        public SocialTokenNotFound() {
            super(ErrorCode.SOCIAL_TOKEN_NOT_FOUND);
        }

        public SocialTokenNotFound(Map<String, String> inputValueProperties) {
            super(ErrorCode.SOCIAL_TOKEN_NOT_FOUND, inputValueProperties);
        }

    }
}