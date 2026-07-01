package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.common.dto.CategoryCountDto;
import com.everyones.lawmaking.common.dto.PartyBillCountDto;
import com.everyones.lawmaking.common.dto.StatisticsOverviewDto;
import com.everyones.lawmaking.common.dto.StatisticsStageDto;
import com.everyones.lawmaking.domain.entity.Bill;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface StatisticsRepository extends JpaRepository<Bill, String> {

    @Query("SELECT new com.everyones.lawmaking.common.dto.StatisticsOverviewDto(" +
            "COUNT(b), " +
            "SUM(CASE WHEN b.billResult IN ('원안가결', '수정가결') THEN 1 ELSE 0 END), " +
            "SUM(CASE WHEN b.billResult IS NULL THEN 1 ELSE 0 END)) " +
            "FROM Bill b " +
            "WHERE b.assemblyNumber = :assembly " +
            "AND b.ingestStatus = com.everyones.lawmaking.domain.entity.IngestStatusType.READY")
    StatisticsOverviewDto findOverview(@Param("assembly") int assembly);

    @Query("SELECT new com.everyones.lawmaking.common.dto.StatisticsStageDto(" +
            "COUNT(b), " +
            "SUM(CASE WHEN b.stage IN ('위원회 심사', '체계자구 심사', '본회의 심의', '정부이송', '공포') THEN 1 ELSE 0 END), " +
            "SUM(CASE WHEN b.stage IN ('본회의 심의', '정부이송', '공포') THEN 1 ELSE 0 END), " +
            "SUM(CASE WHEN b.stage = '공포' THEN 1 ELSE 0 END)) " +
            "FROM Bill b " +
            "WHERE b.assemblyNumber = :assembly " +
            "AND b.ingestStatus = com.everyones.lawmaking.domain.entity.IngestStatusType.READY")
    StatisticsStageDto findStageFunnel(@Param("assembly") int assembly);

    @Query("SELECT new com.everyones.lawmaking.common.dto.PartyBillCountDto(rp.party.id, rp.party.name, COUNT(b)) " +
            "FROM Bill b JOIN b.representativeProposer rp " +
            "WHERE b.assemblyNumber = :assembly " +
            "AND b.ingestStatus = com.everyones.lawmaking.domain.entity.IngestStatusType.READY " +
            "GROUP BY rp.party.id, rp.party.name " +
            "ORDER BY COUNT(b) DESC")
    List<PartyBillCountDto> findBillCountByParty(@Param("assembly") int assembly);

    @Query("SELECT new com.everyones.lawmaking.common.dto.CategoryCountDto(b.category, COUNT(b)) " +
            "FROM Bill b " +
            "WHERE b.assemblyNumber = :assembly " +
            "AND b.ingestStatus = com.everyones.lawmaking.domain.entity.IngestStatusType.READY " +
            "AND b.category IS NOT NULL " +
            "GROUP BY b.category " +
            "ORDER BY COUNT(b) DESC")
    List<CategoryCountDto> findBillCountByCategory(@Param("assembly") int assembly);

    @Query(value = "SELECT DATE_FORMAT(b.propose_date, '%Y-%m') AS ym, COUNT(*) AS cnt " +
            "FROM Bill b " +
            "WHERE b.assembly_number = :assembly " +
            "AND b.ingest_status = 'READY' " +
            "AND b.propose_date IS NOT NULL " +
            "GROUP BY ym " +
            "ORDER BY ym DESC " +
            "LIMIT :months", nativeQuery = true)
    List<Object[]> findMonthlyTrend(@Param("assembly") int assembly, @Param("months") int months);
}
