package com.everyones.lawmaking.repository.election;

import com.everyones.lawmaking.domain.entity.election.ElectionCandidate;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface ElectionCandidateRepository extends JpaRepository<ElectionCandidate, Long> {

    List<ElectionCandidate> findBySgIdAndSgTypecodeAndSdName(String sgId, Integer sgTypecode, String sdName);

    List<ElectionCandidate> findBySgIdAndSgTypecodeAndSdNameAndWiwName(
            String sgId, Integer sgTypecode, String sdName, String wiwName);

    List<ElectionCandidate> findBySgIdAndSgTypecode(String sgId, Integer sgTypecode);

    @Query("SELECT c FROM ElectionCandidate c LEFT JOIN FETCH c.pledges WHERE c.id = :id")
    Optional<ElectionCandidate> findByIdWithPledges(@Param("id") Long id);

    /** 지역 + 선거종류별 후보자 수 집계 */
    @Query("SELECT c.sdName, COUNT(c) FROM ElectionCandidate c " +
           "WHERE c.sgId = :sgId AND c.sgTypecode = :sgTypecode " +
           "GROUP BY c.sdName")
    List<Object[]> countBySdNameAndSgIdAndSgTypecode(
            @Param("sgId") String sgId, @Param("sgTypecode") Integer sgTypecode);
}
