package com.everyones.lawmaking.global.error;

import java.util.Map;

public class BillException extends CustomException {

    public BillException(ErrorCode errorCode) {
        super(errorCode);
    }
    public BillException(ErrorCode errorCode, Map<String, String> inputValueProperties) {
        super(errorCode, inputValueProperties);
    }

    public static class BillNotFound extends BillException {

        public BillNotFound() {
            super(ErrorCode.BILL_NOT_FOUND);
        }

        public BillNotFound(Map<String, String> inputValueProperties) {
            super(ErrorCode.BILL_NOT_FOUND, inputValueProperties);
        }

    }

    public static class SearchParameterInvalid extends BillException {
        public SearchParameterInvalid() {
            super(ErrorCode.INVALID_QUERY_PARAMETER);
        }
        public SearchParameterInvalid(Map<String, String> inputValueProperties) {
            super(ErrorCode.INVALID_QUERY_PARAMETER, inputValueProperties);
        }
    }
}
