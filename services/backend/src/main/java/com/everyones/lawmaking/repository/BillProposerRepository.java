package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.BillProposer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface BillProposerRepository extends JpaRepository<BillProposer, Long> {
    Long countByCongressmanId(String congressmanId);
}
