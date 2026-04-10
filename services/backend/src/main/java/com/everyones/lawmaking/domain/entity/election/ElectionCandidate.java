package com.everyones.lawmaking.domain.entity.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
@Table(name = "election_candidates")
public class ElectionCandidate {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "huboid", nullable = false, length = 20)
    private String huboid;

    @Column(name = "sg_id", nullable = false, length = 20)
    private String sgId;

    @Column(name = "sg_typecode", nullable = false)
    private Integer sgTypecode;

    @Column(name = "candidate_type", nullable = false, length = 20)
    private String candidateType;

    @Column(name = "sgg_name", nullable = false, length = 100)
    private String sggName;

    @Column(name = "sd_name", nullable = false, length = 50)
    private String sdName;

    @Column(name = "wiw_name", length = 50)
    private String wiwName;

    @Column(name = "giho", length = 10)
    private String giho;

    @Column(name = "giho_sangse", length = 50)
    private String gihoSangse;

    @Column(name = "jd_name", length = 100)
    private String jdName;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    @Column(name = "hanja_name", length = 50)
    private String hanjaName;

    @Column(name = "gender", length = 10)
    private String gender;

    @Column(name = "birthday", length = 10)
    private String birthday;

    @Column(name = "age")
    private Integer age;

    @Column(name = "addr", length = 200)
    private String addr;

    @Column(name = "job_id", length = 10)
    private String jobId;

    @Column(name = "job", length = 200)
    private String job;

    @Column(name = "edu_id", length = 10)
    private String eduId;

    @Column(name = "edu", length = 200)
    private String edu;

    @Column(name = "career1", columnDefinition = "TEXT")
    private String career1;

    @Column(name = "career2", columnDefinition = "TEXT")
    private String career2;

    @Column(name = "regdate", length = 10)
    private String regdate;

    @Column(name = "status", length = 20)
    private String status;

    @Column(name = "normalized_region", length = 100)
    private String normalizedRegion;

    @Column(name = "normalized_election_name", length = 100)
    private String normalizedElectionName;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @ToString.Exclude
    @OneToMany(mappedBy = "candidate", fetch = FetchType.LAZY)
    private List<ElectionPledge> pledges;
}
