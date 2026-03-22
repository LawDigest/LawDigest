package com.everyones.lawmaking.global.error;

import java.util.Map;

public class LikeException extends CustomException {

    public LikeException(ErrorCode errorCode) {
        super(errorCode);
    }
    public LikeException(ErrorCode errorCode, Map<String, String> inputValuesByProperty) {
        super(errorCode, inputValuesByProperty);
    }

    public static class UpdateParameterException extends LikeException {
        public UpdateParameterException() {
            super(ErrorCode.BAD_UPDATE_PARAMETER);
        }
        public UpdateParameterException(Map<String, String> inputValuesByProperty) {
            super(ErrorCode.BAD_UPDATE_PARAMETER, inputValuesByProperty);
        }

    }

}
