package com.everyones.lawmaking.repository.poll;

import com.everyones.lawmaking.domain.entity.poll.PollSurvey;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface PollSurveyRepository extends JpaRepository<PollSurvey, String> {

    List<PollSurvey> findByElectionTypeOrderBySurveyEndDateDesc(String electionType);

    List<PollSurvey> findByElectionTypeAndRegionOrderBySurveyEndDateDesc(String electionType, String region);

    @Query("SELECT p FROM PollSurvey p ORDER BY p.createdDate DESC, p.registrationNumber DESC")
    List<PollSurvey> findFeedItemsFirst(Pageable pageable);

    @Query("SELECT p FROM PollSurvey p " +
           "WHERE (p.createdDate < :cursorDate OR (p.createdDate = :cursorDate AND p.registrationNumber < :cursorId)) " +
           "ORDER BY p.createdDate DESC, p.registrationNumber DESC")
    List<PollSurvey> findFeedItems(
            @Param("cursorDate") LocalDateTime cursorDate,
            @Param("cursorId") String cursorId,
            Pageable pageable);
}
