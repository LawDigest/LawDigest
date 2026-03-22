package com.everyones.lawmaking.global.error;

import lombok.extern.slf4j.Slf4j;
import org.apache.coyote.Response;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    // 400 BAD_REQUEST 에러
    @ExceptionHandler({LikeException.UpdateParameterException.class})
    protected ResponseEntity<ErrorResponse> handleGlobalBadRequestException(final CustomException e) {
        log.error(e.getErrorInfoLog());
        return ResponseEntity.badRequest()
                .body(ErrorResponse.from(e));
    }

    // 404 NotFound 에러
    @ExceptionHandler({PartyException.PartyNotFound.class,
                        VoteRecordException.VoteRecordNotFound.class,
                        UserException.UserNotFoundException.class})
    protected ResponseEntity<ErrorResponse> handleGlobalNotFoundException(final CustomException e) {

        log.error(e.getErrorInfoLog());
        return new ResponseEntity<>(ErrorResponse.from(e), HttpStatus.NOT_FOUND);
    }

    //500 error
    @ExceptionHandler(Exception.class)
    protected ResponseEntity<ErrorResponse> handleInternalServerError(final Exception e) {
        log.error(e.toString());
        return ResponseEntity.internalServerError()
                .body(ErrorResponse.from(ErrorCode.INTERNAL_SERVER_ERROR));
    }
}
