package com.everyones.lawmaking.domain.entity.election;

import com.everyones.lawmaking.domain.entity.BaseEntity;
import com.everyones.lawmaking.domain.entity.User;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Table(
        name = "election_feed_bookmark",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_user_feed",
                columnNames = {"user_id", "feed_type", "feed_item_id"}
        ),
        indexes = @Index(name = "idx_user_created", columnList = "user_id, created_date DESC")
)
public class ElectionFeedBookmark extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    @ToString.Exclude
    private User user;

    @Column(name = "feed_type", nullable = false, length = 20)
    private String feedType;

    @Column(name = "feed_item_id", nullable = false, length = 100)
    private String feedItemId;
}
