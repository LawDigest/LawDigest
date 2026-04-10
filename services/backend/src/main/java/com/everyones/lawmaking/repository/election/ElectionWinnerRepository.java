package com.everyones.lawmaking.repository.election;

import com.everyones.lawmaking.domain.entity.election.ElectionWinner;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ElectionWinnerRepository extends JpaRepository<ElectionWinner, Long> {

    List<ElectionWinner> findBySgIdAndSgTypecodeAndSdName(String sgId, Integer sgTypecode, String sdName);

    List<ElectionWinner> findBySgIdAndSgTypecode(String sgId, Integer sgTypecode);
}
