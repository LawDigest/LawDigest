package com.everyones.lawmaking.repository.election;

import com.everyones.lawmaking.domain.entity.election.ElectionDistrict;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ElectionDistrictRepository extends JpaRepository<ElectionDistrict, Long> {

    List<ElectionDistrict> findBySgIdAndSgTypecode(String sgId, Integer sgTypecode);

    /** 시도 목록 (depth=1) */
    @Query("SELECT d.sdName FROM ElectionDistrict d " +
           "WHERE d.sgId = :sgId AND d.sgTypecode = :sgTypecode " +
           "GROUP BY d.sdName ORDER BY MIN(d.sOrder)")
    List<String> findDistinctSdNameBySgIdAndSgTypecode(
            @Param("sgId") String sgId, @Param("sgTypecode") Integer sgTypecode);

    /** 시도 하위 구시군/선거구 목록 (depth=2) */
    List<ElectionDistrict> findBySgIdAndSgTypecodeAndSdName(
            String sgId, Integer sgTypecode, String sdName);
}
