package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.NotificationCountResponse;
import com.everyones.lawmaking.common.dto.response.NotificationResponse;
import com.everyones.lawmaking.domain.entity.Notification;
import com.everyones.lawmaking.global.error.NotificationException;
import com.everyones.lawmaking.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class NotificationService {

    private final NotificationRepository notificationRepository;

    private static final String NOTIFICATION_ID_KEY_LONG = "notificationId";

    public List<NotificationResponse> getNotifications(long userId){
        List<Notification> notifications = notificationRepository.findAllNotificationsByUserIdSorted(userId);

        return NotificationResponse.from(notifications);
    }

    public List<NotificationResponse> getTop3UnreadNotifications(long userId) {
        List<Notification> notifications = notificationRepository.findTop3UnreadNotificationsByUserIdSorted(userId);

        return NotificationResponse.from(notifications);
    }




    public List<NotificationResponse> readNotification(long userId, Optional<Integer> notificationId){
        List<Notification> notifications;
        if (notificationId.isPresent()){
            Notification notification = notificationRepository.findUnreadNotificationByUserId(userId, notificationId.get())
                    .orElseThrow(() -> new NotificationException.NotificationNotFound(Map.of(NOTIFICATION_ID_KEY_LONG, String.valueOf(notificationId.get()))) );
            notification.setRead(true);
            Notification notificationsRead = notificationRepository.save(notification);
            notifications = List.of(notificationsRead);
        }
        else {
            notifications = notificationRepository.findAllUnreadNotificationsByUserId(userId);
            notifications.forEach((noti) -> noti.setRead(true));
            List<Notification> notificationsRead = notificationRepository.saveAll(notifications);
            notifications = notificationsRead;
        }

        return NotificationResponse.from(notifications);
    }

    public String deleteAllNotifications(long userId){
        List<Notification> notifications = notificationRepository.findAllNotificationsByUser(userId);

        notificationRepository.deleteAll(notifications);
        return "success";
    }

    public String deleteNotification(long userId, int notificationId){
        Notification notification = notificationRepository.findNotificationByUserId(userId, notificationId)
                .orElseThrow(() -> new NotificationException.NotificationNotFound(Map.of(NOTIFICATION_ID_KEY_LONG, String.valueOf(notificationId))));


        notificationRepository.delete(notification);
        return "success";
    }

    public void deleteNotificationByUserId(Long userId){
        notificationRepository.deleteAllByUserId(userId);
    }

    public NotificationCountResponse countNotifications(long userId){
        Integer notification = notificationRepository.countNewNotificationsByUserId(userId);
        return NotificationCountResponse.of(userId, notification);
    }




}
