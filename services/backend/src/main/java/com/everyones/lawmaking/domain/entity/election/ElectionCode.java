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
@Table(name = "election_codes")
public class ElectionCode {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "sg_id", nullable = false, length = 20)
    private String sgId;

    @Column(name = "sg_typecode", nullable = false)
    private Integer sgTypecode;

    @Column(name = "sg_name", nullable = false, length = 100)
    private String sgName;

    @Column(name = "sg_vote_date", length = 10)
    private String sgVoteDate;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
