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
@Table(name = "election_winners")
public class ElectionWinner {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "candidate_id")
    @ToString.Exclude
    private ElectionCandidate candidate;

    @Column(name = "huboid", nullable = false, length = 20)
    private String huboid;

    @Column(name = "sg_id", nullable = false, length = 20)
    private String sgId;

    @Column(name = "sg_typecode", nullable = false)
    private Integer sgTypecode;

    @Column(name = "sgg_name", nullable = false, length = 100)
    private String sggName;

    @Column(name = "sd_name", nullable = false, length = 50)
    private String sdName;

    @Column(name = "wiw_name", length = 50)
    private String wiwName;

    @Column(name = "giho", length = 10)
    private String giho;

    @Column(name = "jd_name", length = 100)
    private String jdName;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    @Column(name = "gender", length = 10)
    private String gender;

    @Column(name = "birthday", length = 10)
    private String birthday;

    @Column(name = "age")
    private Integer age;

    @Column(name = "dugsu")
    private Integer dugsu;

    @Column(name = "dugyul", length = 10)
    private String dugyul;

    @Column(name = "normalized_region", length = 100)
    private String normalizedRegion;

    @Column(name = "normalized_election_name", length = 100)
    private String normalizedElectionName;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
