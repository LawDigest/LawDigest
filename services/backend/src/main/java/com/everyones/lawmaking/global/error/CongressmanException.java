package com.everyones.lawmaking.global.error;

import java.util.Map;

public class CongressmanException extends CustomException {

    public CongressmanException(ErrorCode errorCode) {
        super(errorCode);
    }

    public CongressmanException(ErrorCode errorCode, Map<String, String> inputValuesByProperty) {
        super(errorCode, inputValuesByProperty);
    }

    public static class CongressmanNotFound extends CongressmanException {

        public CongressmanNotFound() {
            super(ErrorCode.CONGRESSMAN_NOT_FOUND);
        }

        public CongressmanNotFound(Map<String, String> inputValuesByProperty) {
            super(ErrorCode.CONGRESSMAN_NOT_FOUND, inputValuesByProperty);
        }

    }

    public static class SearchParameterInvalid extends CongressmanException {
        public SearchParameterInvalid() {
            super(ErrorCode.INVALID_QUERY_PARAMETER);
        }
        public SearchParameterInvalid(Map<String, String> inputValueProperties) {
            super(ErrorCode.INVALID_QUERY_PARAMETER, inputValueProperties);
        }
    }
}
