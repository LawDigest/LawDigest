package com.everyones.lawmaking.domain.entity;

import com.everyones.lawmaking.common.dto.request.VoteDfRequest;
import com.everyones.lawmaking.common.dto.request.VotePartyRequest;
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
public class VoteParty extends BaseEntity{

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "vote_party_id")
    private long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "bill_id")
    private Bill bill;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "party_id")
    private Party party;

    @NotNull
    @Column(name="votes_for_count")
    private Integer voteForCount;

    public static VoteParty of(Bill foundBill, Party foundParty, VotePartyRequest votePartyRequest){
        return VoteParty.builder()
                .bill(foundBill)
                .party(foundParty)
                .voteForCount(votePartyRequest.getVoteForCount())
                .build();
    }

    public void updateVotesForCount(VotePartyRequest votePartyRequest){
        this.setVoteForCount(votePartyRequest.getVoteForCount());
    }


}
