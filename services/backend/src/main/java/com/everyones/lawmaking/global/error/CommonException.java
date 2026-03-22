package com.everyones.lawmaking.global.error;

import com.fasterxml.jackson.core.JsonProcessingException;

import java.util.Map;

public class CommonException extends CustomException {
    public CommonException(ErrorCode errorCode) {
        super(errorCode);
    }
    public CommonException(ErrorCode errorCode, Map<String, String> inputValueProperties) {
        super(errorCode, inputValueProperties);
    }

    public static class JsonParsingException extends CommonException {
        public JsonParsingException() {
            super(ErrorCode.JSON_PARSING_ERROR);
        }
    }

}
