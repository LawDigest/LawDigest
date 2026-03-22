package com.everyones.lawmaking.service;

import com.everyones.lawmaking.repository.RepresentativeProposerRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class RepresentativeProposerService {
    private final RepresentativeProposerRepository representativeProposerRepository;

    public Integer countBillByCongressmanAsPublicProposer(String congressmanId) {
        return representativeProposerRepository.countByCongressmanId(congressmanId).intValue();
    }
}
