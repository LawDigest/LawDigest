package com.everyones.lawmaking.controller;

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
import com.everyones.lawmaking.global.BaseResponse;
import com.everyones.lawmaking.service.StatisticsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RequiredArgsConstructor
@RestController
@RequestMapping("/v1/statistics")
@Tag(name = "입법 통계 조회 API", description = "제22대 국회 입법 데이터 집계 통계를 가져오는 API입니다.")
public class StatisticsController {

    private final StatisticsService statisticsService;

    @Operation(summary = "통계 개요(KPI)", description = "제22대 총 발의/가결/계류/가결률을 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/overview")
    public BaseResponse<StatisticsOverviewDto> getOverview() {
        return BaseResponse.ok(statisticsService.getOverview());
    }

    @Operation(summary = "진행 단계 퍼널", description = "제22대 법안의 접수→위원회 심사→본회의 심의→공포 누적 도달 건수를 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/stage")
    public BaseResponse<StatisticsStageDto> getStageFunnel() {
        return BaseResponse.ok(statisticsService.getStageFunnel());
    }

    @Operation(summary = "정당별 발의 건수", description = "제22대 정당별 대표발의 법안 수를 내림차순으로 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/by-party")
    public BaseResponse<List<PartyBillCountDto>> getBillCountByParty() {
        return BaseResponse.ok(statisticsService.getBillCountByParty());
    }

    @Operation(summary = "분야별 분포", description = "제22대 분야(category)별 법안 수를 내림차순으로 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/by-category")
    public BaseResponse<List<CategoryCountDto>> getBillCountByCategory() {
        return BaseResponse.ok(statisticsService.getBillCountByCategory());
    }

    @Operation(summary = "월별 발의 추이", description = "제22대 최근 N개월 월별 발의 건수를 시간순으로 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/trend")
    public BaseResponse<List<MonthlyTrendDto>> getMonthlyTrend(
            @Parameter(example = "6", description = "가져올 개월 수입니다.")
            @RequestParam(name = "months", defaultValue = "6") int months) {
        return BaseResponse.ok(statisticsService.getMonthlyTrend(months));
    }

    @Operation(summary = "정당별 발의·가결 실적", description = "제22대 정당별 대표발의 수, 가결 수, 가결률을 발의 수 내림차순으로 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/party-performance")
    public BaseResponse<List<PartyPerformanceDto>> getPartyPerformance() {
        return BaseResponse.ok(statisticsService.getPartyPerformance());
    }

    @Operation(summary = "월별 발의·가결 추이", description = "제22대 최근 N개월 월별 발의 건수와 그중 가결된 건수를 시간순으로 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/trend-detail")
    public BaseResponse<List<MonthlyTrendDetailDto>> getMonthlyTrendDetail(
            @Parameter(example = "12", description = "가져올 개월 수입니다.")
            @RequestParam(name = "months", defaultValue = "12") int months) {
        return BaseResponse.ok(statisticsService.getMonthlyTrendDetail(months));
    }

    @Operation(summary = "위원회별 법안 수", description = "제22대 소관 위원회별 법안 수와 가결 수를 내림차순으로 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/by-committee")
    public BaseResponse<List<CommitteeCountDto>> getBillCountByCommittee() {
        return BaseResponse.ok(statisticsService.getBillCountByCommittee());
    }

    @Operation(summary = "분야×정당 교차 집계", description = "제22대 분야별로 각 정당의 대표발의 법안 수를 집계합니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/category-party")
    public BaseResponse<List<CategoryPartyCountDto>> getCategoryPartyMatrix() {
        return BaseResponse.ok(statisticsService.getCategoryPartyMatrix());
    }

    @Operation(summary = "처리 결과 분포", description = "제22대 법안 처리 결과(원안가결/수정가결/대안반영폐기 등)별 건수를 집계합니다. 결과 미정은 '계류'로 내려갑니다.")
    @ApiResponses(@ApiResponse(responseCode = "200", description = "조회 성공"))
    @GetMapping("/result-breakdown")
    public BaseResponse<List<ResultBreakdownDto>> getResultBreakdown() {
        return BaseResponse.ok(statisticsService.getResultBreakdown());
    }
}
