package com.everyones.lawmaking.repository.election;

import com.everyones.lawmaking.domain.entity.election.ElectionPledge;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface ElectionPledgeRepository extends JpaRepository<ElectionPledge, Long> {

    @Query("SELECT p FROM ElectionPledge p LEFT JOIN FETCH p.candidate " +
           "WHERE p.sgId = :sgId " +
           "ORDER BY p.createdAt DESC, p.id DESC")
    List<ElectionPledge> findFeedItemsFirst(@Param("sgId") String sgId, Pageable pageable);

    @Query("SELECT p FROM ElectionPledge p LEFT JOIN FETCH p.candidate " +
           "WHERE p.sgId = :sgId AND " +
           "(p.createdAt < :cursorDate OR (p.createdAt = :cursorDate AND p.id < :cursorId)) " +
           "ORDER BY p.createdAt DESC, p.id DESC")
    List<ElectionPledge> findFeedItems(
            @Param("sgId") String sgId,
            @Param("cursorDate") LocalDateTime cursorDate,
            @Param("cursorId") Long cursorId,
            Pageable pageable);
}
