package com.everyones.lawmaking.global.error;

import java.util.Map;

public class AuthException extends CustomException {

    public AuthException(ErrorCode errorCode) {
        super(errorCode);
    }

    public AuthException(ErrorCode errorCode, Map<String, String> inputValueProperties) {
        super(errorCode, inputValueProperties);
    }

    public static class CookieNotFound extends AuthException {
        public CookieNotFound() {
            super(ErrorCode.COOKIE_NOT_FOUND);
        }
        public CookieNotFound(Map<String, String> inputValueProperties) {
            super(ErrorCode.COOKIE_NOT_FOUND, inputValueProperties);
        }
    }

    public static class ThirdPartyError extends AuthException {
        public ThirdPartyError() {
            super(ErrorCode.THRID_PARTY_ERROR);
        }

        public ThirdPartyError(Map<String, String> inputValueProperties) {
            super(ErrorCode.THRID_PARTY_ERROR, inputValueProperties);
        }
    }

    public static class AuthInfoNotFound extends AuthException {
        public AuthInfoNotFound() {
            super(ErrorCode.AUTH_INFO_NOT_FOUND);
        }
        public AuthInfoNotFound(Map<String, String> inputValueProperties) {
            super(ErrorCode.AUTH_INFO_NOT_FOUND, inputValueProperties);
        }
    }

    public static class TokenNotValid extends AuthException {
        public TokenNotValid() {
            super(ErrorCode.TOKEN_NOT_VALID);
        }

        public TokenNotValid(Map<String, String> inputValueProperties) {
            super(ErrorCode.TOKEN_NOT_VALID, inputValueProperties);
        }
    }


    public static class TokenNotFound extends AuthException {
        public TokenNotFound() {
            super(ErrorCode.TOKEN_NOT_FOUND);
        }

        public TokenNotFound(Map<String, String> inputValueProperties) {
            super(ErrorCode.TOKEN_NOT_FOUND, inputValueProperties);
        }
    }
}
