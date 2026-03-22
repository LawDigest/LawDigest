package com.everyones.lawmaking.global.error;

import java.util.Map;

public class UserException extends CustomException {

    public UserException(ErrorCode errorCode) {
        super(errorCode);
    }
    public UserException(ErrorCode errorCode, Map<String, String> inputValuesByProperty) {
        super(errorCode, inputValuesByProperty);
    }

    public static class UserNotFoundException extends UserException {
        public UserNotFoundException() {
            super(ErrorCode.USER_NOT_FOUND);
        }

        public UserNotFoundException(Map<String, String> inputValuesByProperty) {
            super(ErrorCode.USER_NOT_FOUND, inputValuesByProperty);
        }
    }

    public static class WithdrawalFailureException extends UserException {
        public WithdrawalFailureException() {
            super(ErrorCode.WITHDRAWAL_FAILURE);
        }

        public WithdrawalFailureException(Map<String, String> inputValuesByProperty) {
            super(ErrorCode.WITHDRAWAL_FAILURE, inputValuesByProperty);
        }
    }

    public static class UserDeleteFailureException extends UserException {
        public UserDeleteFailureException() {
            super(ErrorCode.USER_DELETE_FAILURE);
        }

        public UserDeleteFailureException(Map<String, String> inputValuesByProperty) {
            super(ErrorCode.USER_DELETE_FAILURE, inputValuesByProperty);
        }
    }


}
