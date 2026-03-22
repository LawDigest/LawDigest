package com.everyones.lawmaking.global.error;

import java.util.Map;

public class ExternalException extends CustomException {
    public ExternalException(ErrorCode errorCode) {
        super(errorCode);
    }
    public ExternalException(ErrorCode errorCode, Map<String, String> inputValuesByProperty) {
        super(errorCode, inputValuesByProperty);
    }

    public static class ApiException extends ExternalException {
        public ApiException(ErrorCode errorCode) {
            super(errorCode);
        }

        public ApiException(ErrorCode errorCode, Map<String, String> parameters) {
            super(errorCode, parameters);
        }
    }
}
