package com.everyones.lawmaking.common.dto.request;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@AllArgsConstructor
@NoArgsConstructor
public class VoteDfRequest {

    private String billId;

    private Integer totalVoteCount;

    private Integer voteForCount;

    private Integer voteAgainstCount;

    private Integer abstentionCount;
}
