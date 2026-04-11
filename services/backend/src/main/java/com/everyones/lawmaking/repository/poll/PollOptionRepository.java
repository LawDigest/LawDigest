package com.everyones.lawmaking.repository.poll;

import com.everyones.lawmaking.domain.entity.poll.PollOption;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PollOptionRepository extends JpaRepository<PollOption, Long> {

    List<PollOption> findByQuestionIdOrderByOptionIdAsc(Long questionId);
}
