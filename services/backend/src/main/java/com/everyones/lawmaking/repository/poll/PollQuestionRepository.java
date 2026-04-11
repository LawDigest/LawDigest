package com.everyones.lawmaking.repository.poll;

import com.everyones.lawmaking.domain.entity.poll.PollQuestion;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PollQuestionRepository extends JpaRepository<PollQuestion, Long> {

    List<PollQuestion> findByRegistrationNumberOrderByQuestionNumberAsc(String registrationNumber);
}
