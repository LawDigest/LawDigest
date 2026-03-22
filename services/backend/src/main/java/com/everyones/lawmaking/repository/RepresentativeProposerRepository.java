package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.RepresentativeProposer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface RepresentativeProposerRepository extends JpaRepository<RepresentativeProposer,Long> {

    Long countByCongressmanId(String congressmanId);

}
