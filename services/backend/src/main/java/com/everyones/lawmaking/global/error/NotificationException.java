package com.everyones.lawmaking.global.error;

import java.util.Map;

public class NotificationException extends CustomException {
    public NotificationException(ErrorCode errorCode) {
        super(errorCode);
    }
    public NotificationException(ErrorCode errorCode, Map<String, String> inputValueProperties) {
        super(errorCode, inputValueProperties);
    }

    public static class NotificationNotFound extends NotificationException {

        public NotificationNotFound() {
            super(ErrorCode.NOTIFICATION_NOT_FOUND);
        }

        public NotificationNotFound(Map<String, String> inputValueProperties) {
            super(ErrorCode.NOTIFICATION_NOT_FOUND, inputValueProperties);
        }

    }
}
