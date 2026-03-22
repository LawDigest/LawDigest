package com.everyones.lawmaking.global;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
@AllArgsConstructor
public enum ResponseCode {

    OK(200, "요청이 정상적으로 처리되었습니다.");

    private final int code;

    private final String message;



}
