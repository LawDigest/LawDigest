package com.everyones.lawmaking.domain.entity;

import com.everyones.lawmaking.common.dto.request.VoteDfRequest;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.*;

@Entity
@Data
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class VoteRecord extends BaseEntity{

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "vote_record_id")
    private long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "bill_id")
    private Bill bill;

    @NotNull
    @Column(name="total_vote_count")
    private Integer totalVoteCount;

    @NotNull
    @Column(name="votes_for_count")
    private Integer voteForCount;

    @NotNull
    @Column(name="votes_againt_count")
    private Integer voteAgainstCount;

    @NotNull
    @Column(name="abstention_count")
    private Integer abstentionCount;

    public static VoteRecord of(Bill foundBill, VoteDfRequest voteDfRequest){
        return VoteRecord.builder()
                .bill(foundBill)
                .totalVoteCount(voteDfRequest.getTotalVoteCount())
                .voteForCount(voteDfRequest.getVoteForCount())
                .voteAgainstCount(voteDfRequest.getVoteAgainstCount())
                .abstentionCount(voteDfRequest.getAbstentionCount())
                .build();
    }

}
