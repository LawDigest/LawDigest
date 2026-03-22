package com.everyones.lawmaking.global.error;

import lombok.AllArgsConstructor;
import lombok.Getter;

@AllArgsConstructor
@Getter
public enum ErrorCode {

    VOTE_RECORD_NOT_FOUND(404, "법안에 대한 투표 기록을 찾을 수 없습니다."),

    COOKIE_NOT_FOUND(404, "쿠키를 찾을 수 없습니다."),

    THRID_PARTY_ERROR(500, "써드 파티 인증 이용 중 오류가 발생하였습니다."),

    AUTH_INFO_NOT_FOUND(404, "인증 정보를 찾을 수 없습니다."),

    SOCIAL_ID_NOT_EQUAL(400, "소셜 아이디가 일치하지 않습니다."),

    TOKEN_NOT_VALID(400, "토큰이 유효하지 않습니다."),

    TOKEN_NOT_FOUND(404, "토큰데이터를 찾을 수 없습니다."),

    SEARCH_PARAMETER_INVALID(400, "검색 단어가 조건에 부합하지 않습니다."),

    USER_NOT_FOUND(404, "해당 유저를 찾을 수 없습니다."),

    CONGRESSMAN_NOT_FOUND(404, "해당 의원을 찾을 수 없습니다."),

    BILL_NOT_FOUND(404, "해당 법안을 찾을 수 없습니다."),

    PARTY_NOT_FOUND(404, "해당 파티를 찾을 수 없습니다."),

    NOTIFICATION_NOT_FOUND(404, "해당 알림을 찾을 수 없습니다."),

    SOCIAL_TOKEN_NOT_FOUND(404, "해당 소셜 토큰을 찾을 수 없습니다."),
    EXTERNAL_API_ERROR(502, "외부 API 호출 중 오류가 발생하였습니다."),
    WITHDRAWAL_FAILURE(409, "해당 유저의 탈퇴가 실패하였습니다."),
    USER_DELETE_FAILURE(500, "해당 유저의 삭제가 실패하였습니다."),

    // 업데이트를 위해 제공된 파라미터와 DB 내부 값이 일치하여 반환해주는 에러
    BAD_UPDATE_PARAMETER(400, "업데이트 하려는 파라미터와 DB 내부 값이 일치합니다."),

    BAD_REQUEST(400, "잘못된 요청입니다."),

    JSON_PARSING_ERROR(500, "데이터 파싱 오류"),

    INTERNAL_SERVER_ERROR(500, "서버 내부 오류입니다."),

    INVALID_QUERY_PARAMETER(400, "유효하지 않은 쿼리파라미터값이 포함되어있습니다");

    private final int code;
    private final String message;
}
