package com.everyones.lawmaking.service;

import com.everyones.lawmaking.domain.entity.VoteRecord;
import com.everyones.lawmaking.global.error.VoteRecordException;
import com.everyones.lawmaking.repository.VoteRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class VoteRecordService {
    private final VoteRecordRepository voteRecordRepository;

    //TODO: 본회의 심의로 Timeline 테이블에는 존재하지만 VoteRecord에 없는 법안이 존재
    public VoteRecord getVoteRecordByBillId(String billId) {
        return voteRecordRepository.findVoteRecordByBillId(billId)
                .orElse(null);
    }
}
