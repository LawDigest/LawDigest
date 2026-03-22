package com.everyones.lawmaking.global.util;

import com.everyones.lawmaking.common.dto.response.NotificationResponse;
import com.everyones.lawmaking.domain.entity.ColumnEventType;
import com.everyones.lawmaking.domain.entity.Notification;
import com.everyones.lawmaking.domain.entity.ProposerKindType;
import com.everyones.lawmaking.global.error.CommonException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Component
public class NotificationConverter {

    // NotificationResponse를 만드는 메소드가 static 메소드 이기에 안에 들어가는 객체들도 전부 static이어야 함.
    // static을 하지 않으면 사용하는 객체를 생성할 때 facade를 계속 의존성 주입 해줘야함
    // 그런데 NotificationResponse Dto 클래스에 Facade 의존성 주입을 해주는 것이 클래스 목적성을 흐린다고 생각하여 해당 클래스를 만듦.
    // 따라서 처음에 facade를 static으로 선언 된 것을 필드 주입을 통해서 facade 인스턴스를 초기화


    private static final ObjectMapper mapper = new ObjectMapper();

    private static List<String> parseData(String data) {
        try {
            return mapper.readValue(data, new TypeReference<List<String>>() {
            });
        } catch (JsonProcessingException e) {
            throw new CommonException.JsonParsingException();
        }
    }

    /* TODO: 객체 기능좀 나누는게 좋지 않을까 싶습니다.
    응답 객체를 만드는 기능의 static 메소드인데 너무 뚱뚱함. 다이어트 필요해보임.
    그리고 해당 Response 객체 생성 자체도 NotificationResponse객체에서 하게 하는게 맞는 것 같아 보임.
    */
    public static NotificationResponse from(Notification notification) {
        ColumnEventType columnEventType = ColumnEventType.findByEventName(notification.getNotificationName());
        List<String> data = parseData(notification.getContentJson());
        Long notificationId = notification.getId();
        String type = columnEventType.getEventName();
        String target = data.get(0);
        boolean isRead = notification.isRead();
        String title = null;
        String content = null;
        String extra = null;
        List<String> notificationImageUrlList = new ArrayList<>();
        switch (columnEventType) {
            case RP_INSERT:

                title = data.get(1) + " 의원";
                content = "'"+data.get(2) + "' 법안을 대표 발의했어요!";
                notificationImageUrlList.addAll(data.subList(3, data.size()));
                break;
            case BILL_STAGE_UPDATE:

                title = data.get(1);
                content = "심사 단계가 '" + data.get(2) + "'로 변동했어요!";
                extra = data.get(3);
                if(data.get(3).equals(ProposerKindType.CONGRESSMAN.name())){
                    notificationImageUrlList.addAll(data.subList(4, data.size()));
                }else{
                    notificationImageUrlList.add(data.get(4)+".png");
                }
                break;
            case BILL_RESULT_UPDATE:

                title = data.get(1);
                content = "'"+data.get(2) + "'로 처리되었어요!";
                extra = data.get(3);
                if(data.get(3).equals(ProposerKindType.CONGRESSMAN.name())){
                    notificationImageUrlList.addAll(data.subList(4, data.size()));
                }else{
                    notificationImageUrlList.add(data.get(4)+".png");
                }
                break;
            case CONGRESSMAN_PARTY_UPDATE:
                title = data.get(2);
                content = "'"+data.get(2)+"'의원의 당적이 '"+data.get(1)+"' 정당으로 변동했어요!";
                notificationImageUrlList.add(data.get(3));
                break;
        }

        LocalDateTime createdDate = notification.getCreatedDate();

        if (type == null || target == null || title == null || content == null || createdDate.isAfter(LocalDateTime.now())) {
            throw new CommonException.JsonParsingException();
        }


        return NotificationResponse.builder()
                // 이벤트 타입
                .type(type)
                // 알림 id값
                .notificationId(notificationId)
                // 알림으로 이동할 대상 id값
                .isRead(isRead)
                .target(target)
                .notificationImageUrlList(notificationImageUrlList)
                .title(title)
                .content(content)
                .createdDate(createdDate.toLocalDate())
                .extra(extra)
                .build();
    }

}
