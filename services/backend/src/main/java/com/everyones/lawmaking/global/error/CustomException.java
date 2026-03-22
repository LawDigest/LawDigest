package com.everyones.lawmaking.global.error;

import com.everyones.lawmaking.global.ResponseCode;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.ToString;

import java.util.Collections;
import java.util.Map;
import java.util.stream.Collectors;

@AllArgsConstructor
@Getter
@ToString
public class CustomException extends RuntimeException {

    private final int code;
    private final String message;
    private final Map<String, String> inputValuesByProperty;
    static class ErrorConstant{
        static final String EXCEPTION_INFO_BRACKET = "{ %s | %s }";
        static final String CODE_MESSAGE = " Code: %d, Message: %s ";
        static final String PROPERTY_VALUE = "Property: %s, Value: %s ";
        static final String VALUE_DELIMITER = "/";
    }

    // CustomException을 protected로 생성한 이유는 직접적으로 CustomException을 생성하는 것을 방지하기 위함.
    // CustomeException을 상속 받은 다른 에러계층에서 생성할 수 있게 하기 위함.
    protected CustomException(final ErrorCode errorCode) {
        this(errorCode, Collections.emptyMap());
    }

    protected CustomException(final ErrorCode errorCode, final Map<String, String> inputValuesByProperty) {
        this.code = errorCode.getCode();
        this.message = errorCode.getMessage();
        this.inputValuesByProperty = inputValuesByProperty;
    }

    public String getErrorInfoLog() {
        final String codeMessage = String.format(ErrorConstant.CODE_MESSAGE, code, message);
        final String errorPropertyValue = getErrorPropertyValue();

        return String.format(ErrorConstant.EXCEPTION_INFO_BRACKET, codeMessage, errorPropertyValue);
    }

    private String getErrorPropertyValue() {

        return inputValuesByProperty.entrySet()
                .stream()
                .map(entry -> String.format(ErrorConstant.PROPERTY_VALUE, entry.getKey(), entry.getValue()))
                .collect(Collectors.joining(ErrorConstant.VALUE_DELIMITER));
    }
}
