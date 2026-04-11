package com.everyones.lawmaking.repository.poll;

import com.everyones.lawmaking.domain.entity.poll.PollSurvey;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PollSurveyRepository extends JpaRepository<PollSurvey, String> {

    List<PollSurvey> findByElectionTypeOrderBySurveyEndDateDesc(String electionType);

    List<PollSurvey> findByElectionTypeAndRegionOrderBySurveyEndDateDesc(String electionType, String region);
}
