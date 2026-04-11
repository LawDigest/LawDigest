package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.election.*;
import com.everyones.lawmaking.global.BaseResponse;
import com.everyones.lawmaking.service.election.ElectionService;
import com.everyones.lawmaking.service.election.poll.PollQueryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RequiredArgsConstructor
@RestController
@RequestMapping("/v1/election")
@Tag(name = "선거 API", description = "선거 데이터 조회 API")
public class ElectionController {

    private final ElectionService electionService;
    private final PollQueryService pollQueryService;

    @Operation(summary = "선거 선택기", description = "전체 선거 목록과 기본 선거 ID를 반환합니다.")
    @GetMapping("/selector")
    public BaseResponse<ElectionSelectorResponse> getSelector() {
        return BaseResponse.ok(electionService.getSelector());
    }

    @Operation(summary = "선거 개요", description = "선거 UI 템플릿과 기본 결과 카드를 반환합니다.")
    @GetMapping("/overview")
    public BaseResponse<ElectionOverviewResponse> getOverview(
            @RequestParam("election_id") String electionId,
            @RequestParam(value = "region_type", required = false) String regionType,
            @RequestParam(value = "region_code", required = false) String regionCode) {
        return BaseResponse.ok(electionService.getOverview(electionId, regionType, regionCode));
    }

    @Operation(summary = "여론조사 개요", description = "선거와 지역 기준의 여론조사 overview 데이터를 반환합니다.")
    @GetMapping("/polls/overview")
    public BaseResponse<ElectionPollOverviewResponse> getPollOverview(
            @RequestParam("election_id") String electionId,
            @RequestParam("region_code") String regionCode) {
        return BaseResponse.ok(pollQueryService.getOverview(electionId, regionCode));
    }

    @Operation(summary = "지도 데이터", description = "지역별 후보자 수 등 지도 표시용 데이터를 반환합니다.")
    @GetMapping("/map")
    public BaseResponse<ElectionMapResponse> getMap(
            @RequestParam("election_id") String electionId,
            @RequestParam(value = "depth", required = false) Integer depth,
            @RequestParam(value = "region_code", required = false) String regionCode,
            @RequestParam(value = "view_mode", required = false) String viewMode) {
        return BaseResponse.ok(electionService.getMap(electionId, depth, regionCode, viewMode));
    }

    @Operation(summary = "지역 패널", description = "선택된 지역의 선거종류별 후보자 수 요약을 반환합니다.")
    @GetMapping("/region-panel")
    public BaseResponse<ElectionRegionPanelResponse> getRegionPanel(
            @RequestParam("election_id") String electionId,
            @RequestParam(value = "depth", required = false) Integer depth,
            @RequestParam(value = "region_code", required = false) String regionCode,
            @RequestParam(value = "office_type", required = false) String officeType) {
        return BaseResponse.ok(electionService.getRegionPanel(electionId, depth, regionCode, officeType));
    }

    @Operation(summary = "후보자 목록", description = "지역/선거종류별 후보자 목록을 반환합니다.")
    @GetMapping("/candidates")
    public BaseResponse<ElectionCandidateListResponse> getCandidates(
            @RequestParam("election_id") String electionId,
            @RequestParam(value = "region_code", required = false) String regionCode,
            @RequestParam(value = "office_type", required = false) String officeType) {
        return BaseResponse.ok(electionService.getCandidates(electionId, regionCode, officeType));
    }

    @Operation(summary = "후보자 상세", description = "후보자의 상세 정보와 공약을 반환합니다.")
    @GetMapping("/candidates/{candidateId}")
    public BaseResponse<ElectionCandidateDetailResponse> getCandidateDetail(
            @PathVariable Long candidateId,
            @RequestParam(value = "election_id", required = false) String electionId) {
        return BaseResponse.ok(electionService.getCandidateDetail(candidateId, electionId));
    }

    @Operation(summary = "지역 결정", description = "GPS 좌표 또는 지역명으로 선거구를 결정합니다.")
    @PostMapping("/regions/resolve")
    public BaseResponse<ElectionRegionResolveResponse> resolveRegion(
            @RequestBody Map<String, String> body) {
        return BaseResponse.ok(electionService.resolveRegion(
                body.get("election_id"),
                body.get("region_code"),
                body.get("region_name")));
    }

    @Operation(summary = "지역 확정", description = "선택된 지역을 확정합니다.")
    @PostMapping("/regions/confirm")
    public BaseResponse<ElectionRegionResolveResponse> confirmRegion(
            @RequestBody Map<String, String> body) {
        return BaseResponse.ok(electionService.confirmRegion(
                body.get("election_id"),
                body.get("region_code"),
                body.get("region_name")));
    }
}
