package com.everyones.lawmaking.repository.election;

import com.everyones.lawmaking.domain.entity.election.ElectionCode;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface ElectionCodeRepository extends JpaRepository<ElectionCode, Long> {

    /** sgTypecode=0 (대표선거명)만 조회 → 선거 목록용 */
    @Query("SELECT e FROM ElectionCode e WHERE e.sgTypecode = 0 ORDER BY e.sgVoteDate DESC")
    List<ElectionCode> findAllRepresentativeElections();

    List<ElectionCode> findBySgId(String sgId);
}
