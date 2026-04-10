package com.everyones.lawmaking.domain.entity.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
@Table(name = "election_pledges")
public class ElectionPledge {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "candidate_id")
    @ToString.Exclude
    private ElectionCandidate candidate;

    @Column(name = "sg_id", nullable = false, length = 20)
    private String sgId;

    @Column(name = "sg_typecode", nullable = false)
    private Integer sgTypecode;

    @Column(name = "cnddt_id", nullable = false, length = 20)
    private String cnddtId;

    @Column(name = "prms_ord", nullable = false)
    private Integer prmsOrd;

    @Column(name = "prms_title", columnDefinition = "TEXT")
    private String prmsTitle;

    @Column(name = "prms_content", columnDefinition = "TEXT")
    private String prmsContent;

    @Column(name = "normalized_region", length = 100)
    private String normalizedRegion;

    @Column(name = "normalized_election_name", length = 100)
    private String normalizedElectionName;

    @Column(name = "summary", columnDefinition = "TEXT")
    private String summary;

    @Column(name = "embedding_id", length = 100)
    private String embeddingId;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
