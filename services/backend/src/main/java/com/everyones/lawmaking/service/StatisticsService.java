package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.CategoryCountDto;
import com.everyones.lawmaking.common.dto.CategoryPartyCountDto;
import com.everyones.lawmaking.common.dto.CommitteeCountDto;
import com.everyones.lawmaking.common.dto.MonthlyTrendDetailDto;
import com.everyones.lawmaking.common.dto.MonthlyTrendDto;
import com.everyones.lawmaking.common.dto.PartyBillCountDto;
import com.everyones.lawmaking.common.dto.PartyPerformanceDto;
import com.everyones.lawmaking.common.dto.ResultBreakdownDto;
import com.everyones.lawmaking.common.dto.StatisticsOverviewDto;
import com.everyones.lawmaking.common.dto.StatisticsStageDto;
import com.everyones.lawmaking.global.constant.BillInfoConstant;
import com.everyones.lawmaking.repository.StatisticsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class StatisticsService {

    private final StatisticsRepository statisticsRepository;

    private int currentAssembly() {
        return BillInfoConstant.getCurrentAssemblyNumber();
    }

    public StatisticsOverviewDto getOverview() {
        return statisticsRepository.findOverview(currentAssembly());
    }

    public StatisticsStageDto getStageFunnel() {
        return statisticsRepository.findStageFunnel(currentAssembly());
    }

    public List<PartyBillCountDto> getBillCountByParty() {
        return statisticsRepository.findBillCountByParty(currentAssembly());
    }

    public List<CategoryCountDto> getBillCountByCategory() {
        return statisticsRepository.findBillCountByCategory(currentAssembly());
    }

    public List<MonthlyTrendDto> getMonthlyTrend(int months) {
        // 네이티브 쿼리는 최신월부터(DESC) 내려주므로, 시간순(오름차순)으로 뒤집어 반환한다.
        var rows = statisticsRepository.findMonthlyTrend(currentAssembly(), months);
        var trend = new ArrayList<MonthlyTrendDto>(rows.size());
        for (int i = rows.size() - 1; i >= 0; i--) {
            Object[] row = rows.get(i);
            trend.add(new MonthlyTrendDto((String) row[0], ((Number) row[1]).longValue()));
        }
        return trend;
    }

    public List<PartyPerformanceDto> getPartyPerformance() {
        return statisticsRepository.findPartyPerformance(currentAssembly());
    }

    public List<MonthlyTrendDetailDto> getMonthlyTrendDetail(int months) {
        // 네이티브 쿼리는 최신월부터(DESC) 내려주므로, 시간순(오름차순)으로 뒤집어 반환한다.
        var rows = statisticsRepository.findMonthlyTrendDetail(currentAssembly(), months);
        var trend = new ArrayList<MonthlyTrendDetailDto>(rows.size());
        for (int i = rows.size() - 1; i >= 0; i--) {
            Object[] row = rows.get(i);
            trend.add(new MonthlyTrendDetailDto(
                    (String) row[0],
                    ((Number) row[1]).longValue(),
                    ((Number) row[2]).longValue()));
        }
        return trend;
    }

    public List<CommitteeCountDto> getBillCountByCommittee() {
        return statisticsRepository.findBillCountByCommittee(currentAssembly());
    }

    public List<CategoryPartyCountDto> getCategoryPartyMatrix() {
        return statisticsRepository.findCategoryPartyMatrix(currentAssembly());
    }

    public List<ResultBreakdownDto> getResultBreakdown() {
        return statisticsRepository.findResultBreakdown(currentAssembly());
    }
}
