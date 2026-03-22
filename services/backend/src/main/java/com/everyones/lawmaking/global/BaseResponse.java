package com.everyones.lawmaking.global;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.experimental.SuperBuilder;
import org.springframework.http.HttpStatus;

@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
@Getter
@SuperBuilder
@Schema(description="API 응답 최상위 오브젝트")
public class BaseResponse<T> {

    @Schema(description = "성공 여부")
    private HttpStatus status;
    @Schema(description = "응답 코드 (HTTP 코드와 동일)", defaultValue = "200")
    private int code;
    @Schema(description = "응답 메시지 (오류시 오류메시지 전달용)", defaultValue = "정상적으로 처리되었습니다.")
    private String message;
    @Schema(description = "응답 본문 오브젝트")
    private T data;

    public static <T> BaseResponse<T> ok(T data) {
        return BaseResponse.<T>builder()
                .code(ResponseCode.OK.getCode())
                .status(HttpStatus.OK)
                .message(ResponseCode.OK.getMessage())
                .data(data)
                .build();
    }

    // 메시지를 따로 담고 싶을 때 사용
    public static <T> BaseResponse ok(T data, String message) {
        return BaseResponse.builder()
                .code(ResponseCode.OK.getCode())
                .status(HttpStatus.OK)
                .message(message)
                .data(data)
                .build();
    }

}
