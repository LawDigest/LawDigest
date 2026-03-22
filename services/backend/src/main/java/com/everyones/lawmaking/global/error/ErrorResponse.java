package com.everyones.lawmaking.global.error;

import com.everyones.lawmaking.global.ResponseCode;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import org.springframework.http.HttpStatus;

import java.time.LocalDateTime;

@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
@Getter
@Builder
@AllArgsConstructor
@Schema(description="API 에러 반환 오브젝트")
public class ErrorResponse {
    @Schema(description = "에러 발생 시각")
    private LocalDateTime time;
    @Schema(description = "성공 여부", example = "false")
    private HttpStatus status;
    @Schema(description = "응답 코드 (HTTP 코드와 동일)", defaultValue = "500")
    private int code;
    @Schema(description = "응답 메시지 (오류시 오류메시지 전달용)", defaultValue = "해당 데이터가 존재하지 않습니다.")
    private String message;

    public static ErrorResponse from(ErrorCode errorCode) {
        return ErrorResponse.builder()
                .time(LocalDateTime.now())
                .status(HttpStatus.valueOf(errorCode.getCode()))
                .code(errorCode.getCode())
                .message(errorCode.getMessage())
                .build();
    }

    public static ErrorResponse from(CustomException customException) {
        return ErrorResponse.builder()
                .time(LocalDateTime.now())
                .status(HttpStatus.valueOf(customException.getCode()))
                .code(customException.getCode())
                .message(customException.getMessage())
                .build();
    }

}