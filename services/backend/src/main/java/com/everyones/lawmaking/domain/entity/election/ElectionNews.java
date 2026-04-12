package com.everyones.lawmaking.domain.entity.election;

import com.everyones.lawmaking.domain.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Table(
        name = "election_news",
        uniqueConstraints = @UniqueConstraint(name = "uk_news_link", columnNames = {"link"}),
        indexes = @Index(name = "idx_election_pubdate", columnList = "election_id, pub_date DESC")
)
public class ElectionNews extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "election_id", nullable = false, length = 50)
    private String electionId;

    @Column(name = "title", nullable = false, length = 500)
    private String title;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "link", nullable = false, length = 1000)
    private String link;

    @Column(name = "original_link", length = 1000)
    private String originalLink;

    @Column(name = "source", length = 100)
    private String source;

    @Column(name = "thumbnail_url", length = 1000)
    private String thumbnailUrl;

    @Column(name = "pub_date", nullable = false)
    private LocalDateTime pubDate;

    @Column(name = "search_keyword", length = 200)
    private String searchKeyword;

    @Column(name = "matched_party", length = 100)
    private String matchedParty;

    @Column(name = "matched_region", length = 100)
    private String matchedRegion;
}
