package com.everyones.lawmaking.service;

import com.everyones.lawmaking.repository.BillProposerRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class BillProposerService {
    private final BillProposerRepository billProposerRepository;

    public Integer countBillByCongressmanAsPublicProposer(String congressmanId) {
        return billProposerRepository.countByCongressmanId(congressmanId).intValue();
    }
}
