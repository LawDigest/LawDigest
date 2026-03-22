package com.everyones.lawmaking.global.config;

import com.everyones.lawmaking.domain.entity.ColumnEventType;
import com.everyones.lawmaking.domain.entity.Notification;
import com.everyones.lawmaking.domain.entity.User;
import com.everyones.lawmaking.facade.NotificationFacade;
import com.everyones.lawmaking.global.error.CommonException;
import com.everyones.lawmaking.repository.NotificationRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
@Slf4j
@RequiredArgsConstructor
public class NotificationCreator {

    private final NotificationRepository notificationRepository;
    private final NotificationFacade notificationFacade;
    private final ObjectMapper objectMapper = new ObjectMapper();

    //ToDo: 알림 데이터 삽입 시 유니크키 컬럼을 추가해서 다중 스프링서버환경에서도 중복 데이터가 삽입되지 않도록 처리
    @Transactional
    public void createNotification(List<Map<String, List<String>>> filteredValuesByRows) {
        if (filteredValuesByRows == null || filteredValuesByRows.isEmpty()) {
            // filteredValuesByRows 자체가 비어있다면 작업 생략
            log.warn("filteredValuesByRows is empty, skipping notification creation.");
            return;
        }
        List<Notification> notifications = new ArrayList<>();
        filteredValuesByRows.forEach((eventDataByEventTypeMap) -> {
            if (eventDataByEventTypeMap == null || eventDataByEventTypeMap.isEmpty()) {
                // Map이 비어있다면 건너뜀
                log.warn("EventDataByEventTypeMap is empty, skipping.");
                return;
            }
            eventDataByEventTypeMap.forEach((eventType, eventData) -> {
                if (eventData == null || eventData.isEmpty()) {
                    log.warn("EventData is empty for eventType: {}", eventType);
                    return; // 비어 있으면 작업 생략
                }
                try {
                    // eventData의 첫번째 값은 항상 targetId
                    ColumnEventType columnEventType = ColumnEventType.from(eventType);
                    List<User> subscribedSavedUser = notificationFacade.getSubscribedUsers(columnEventType, eventData.get(0));
                    List<String> processedData = notificationFacade.getProcessedData(columnEventType,eventData);
                    if (processedData.isEmpty()) {
                        log.warn("Processed data is empty for eventType: {}", eventType);
                        return;
                    }
                    String jsonString = objectMapper.writeValueAsString(processedData);

                    subscribedSavedUser
                            .forEach(user -> {
                                notifications.add(
                                Notification.builder()
                                        .notificationName(columnEventType.name())
                                        .contentJson(jsonString)
                                        .user(user)
                                        .build());
                            });
                } catch (JsonProcessingException e) {
                    throw new CommonException.JsonParsingException();
                }
            });
                });
        notificationRepository.saveAll(notifications);
    }
}
