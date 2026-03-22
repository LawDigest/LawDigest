package com.everyones.lawmaking.domain.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.*;

@Entity
@Builder
@Getter
@Setter
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Notification extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "notification_id")
    private long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    // 알림 이름(유형)
    @NotNull
    @Column(name = "notification_name")
    private String notificationName;

    // 알림 내용
    @NotNull
    @Column(name = "notification_content_json")
    private String contentJson;

    // 알림을 보냈는지 여부
    @NotNull
    @Column(name = "is_sent")
    private boolean isSent;

    // 사용자가 알림을 읽음 여부
    @NotNull
    @Column(name = "is_read")
    private boolean isRead;


}
