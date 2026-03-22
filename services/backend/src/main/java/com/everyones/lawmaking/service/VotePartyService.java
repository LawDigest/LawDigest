package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.PartyVoteDto;
import com.everyones.lawmaking.domain.entity.VoteParty;
import com.everyones.lawmaking.repository.VotePartyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class VotePartyService {
    private final VotePartyRepository votePartyRepository;

    public List<VoteParty> getVotePartyListWithPartyByBillId(String billId) {
        return votePartyRepository.findVotePartyWithPartyByBillId(billId);
    }
}
