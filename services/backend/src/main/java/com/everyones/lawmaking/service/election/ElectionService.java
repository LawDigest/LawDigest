package com.everyones.lawmaking.service.election;

import com.everyones.lawmaking.common.dto.response.election.*;
import com.everyones.lawmaking.domain.entity.election.ElectionCandidate;
import com.everyones.lawmaking.domain.entity.election.ElectionCode;
import com.everyones.lawmaking.domain.entity.election.ElectionDistrict;
import com.everyones.lawmaking.domain.entity.election.ElectionPledge;
import com.everyones.lawmaking.repository.election.ElectionCandidateRepository;
import com.everyones.lawmaking.repository.election.ElectionCodeRepository;
import com.everyones.lawmaking.repository.election.ElectionDistrictRepository;
import com.everyones.lawmaking.repository.election.ElectionWinnerRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ElectionService {

    private final ElectionCodeRepository electionCodeRepository;
    private final ElectionCandidateRepository candidateRepository;
    private final ElectionDistrictRepository districtRepository;
    private final ElectionWinnerRepository winnerRepository;

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyyMMdd");

    // sgTypecode → 선거종류명
    private static final Map<Integer, String> OFFICE_NAMES = Map.ofEntries(
            Map.entry(1, "대통령선거"),
            Map.entry(2, "국회의원선거"),
            Map.entry(3, "시도지사선거"),
            Map.entry(4, "구시군장선거"),
            Map.entry(5, "시도의원선거"),
            Map.entry(6, "구시군의회의원선거"),
            Map.entry(7, "국회의원비례대표선거"),
            Map.entry(8, "광역의원비례대표선거"),
            Map.entry(9, "기초의원비례대표선거"),
            Map.entry(10, "교육의원선거"),
            Map.entry(11, "교육감선거")
    );

    // ──────────────────────────────────────────
    // 1. Selector
    // ──────────────────────────────────────────

    public ElectionSelectorResponse getSelector() {
        var codes = electionCodeRepository.findAllRepresentativeElections();
        var today = LocalDate.now().format(DATE_FMT);

        // 가장 가까운 미래/현재 선거를 기본값으로
        String defaultId = codes.stream()
                .filter(c -> c.getSgVoteDate() != null && c.getSgVoteDate().compareTo(today) >= 0)
                .min(Comparator.comparing(ElectionCode::getSgVoteDate))
                .map(ElectionCode::getSgId)
                .orElse(codes.isEmpty() ? "" : codes.get(0).getSgId());

        var items = codes.stream()
                .map(c -> ElectionSelectorResponse.ElectionItem.builder()
                        .electionId(c.getSgId())
                        .electionName(c.getSgName())
                        .electionDate(c.getSgVoteDate())
                        .upcoming(c.getSgVoteDate() != null && c.getSgVoteDate().compareTo(today) > 0)
                        .build())
                .toList();

        return ElectionSelectorResponse.builder()
                .defaultElectionId(defaultId)
                .elections(items)
                .build();
    }

    // ──────────────────────────────────────────
    // 2. Overview
    // ──────────────────────────────────────────

    public ElectionOverviewResponse getOverview(String electionId, String regionType, String regionCode) {
        // 지방선거는 REGIONAL, 대선은 CANDIDATE
        var codes = electionCodeRepository.findBySgId(electionId);
        boolean isPresidential = codes.stream().anyMatch(c -> c.getSgTypecode() == 1);
        String uiTemplate = isPresidential ? "CANDIDATE" : "REGIONAL";

        var defaultCard = ElectionOverviewResponse.ElectionResultCardResponse.builder()
                .sourceElectionId(electionId)
                .regionType(regionType != null ? regionType : "PROVINCE")
                .regionCode(regionCode != null ? regionCode : "")
                .title(codes.stream()
                        .filter(c -> c.getSgTypecode() == 0)
                        .findFirst()
                        .map(ElectionCode::getSgName)
                        .orElse("선거"))
                .build();

        return ElectionOverviewResponse.builder()
                .selectedElectionId(electionId)
                .uiTemplate(uiTemplate)
                .defaultResultCard(defaultCard)
                .build();
    }

    // ──────────────────────────────────────────
    // 3. Candidates
    // ──────────────────────────────────────────

    public ElectionCandidateListResponse getCandidates(
            String electionId, String regionCode, String officeType) {
        Integer sgTypecode = officeType != null ? parseTypecode(officeType) : 3; // 기본: 시도지사
        List<ElectionCandidate> candidates;

        if (regionCode != null && !regionCode.isEmpty()) {
            candidates = candidateRepository.findBySgIdAndSgTypecodeAndSdName(
                    electionId, sgTypecode, regionCode);
        } else {
            candidates = candidateRepository.findBySgIdAndSgTypecode(electionId, sgTypecode);
        }

        var items = candidates.stream()
                .map(c -> ElectionCandidateListResponse.CandidateItem.builder()
                        .candidateId(c.getId())
                        .candidateName(c.getName())
                        .partyName(c.getJdName())
                        .candidateImageUrl(null) // 이미지 URL은 현재 DB에 없음
                        .giho(c.getGiho())
                        .status(c.getStatus())
                        .candidateType(c.getCandidateType())
                        .build())
                .toList();

        return ElectionCandidateListResponse.builder()
                .selectedElectionId(electionId)
                .regionCode(regionCode)
                .officeType(officeType)
                .candidates(items)
                .build();
    }

    // ──────────────────────────────────────────
    // 4. Candidate Detail
    // ──────────────────────────────────────────

    public ElectionCandidateDetailResponse getCandidateDetail(Long candidateId, String electionId) {
        var candidate = candidateRepository.findByIdWithPledges(candidateId)
                .orElseThrow(() -> new NoSuchElementException("후보자를 찾을 수 없습니다: id=" + candidateId));

        var manifestoItems = candidate.getPledges() != null
                ? candidate.getPledges().stream()
                    .sorted(Comparator.comparingInt(ElectionPledge::getPrmsOrd))
                    .map(p -> ElectionCandidateDetailResponse.ManifestoItem.builder()
                            .order(p.getPrmsOrd())
                            .title(p.getPrmsTitle())
                            .content(p.getPrmsContent())
                            .build())
                    .toList()
                : List.<ElectionCandidateDetailResponse.ManifestoItem>of();

        return ElectionCandidateDetailResponse.builder()
                .selectedElectionId(electionId != null ? electionId : candidate.getSgId())
                .candidateId(candidate.getId())
                .candidateName(candidate.getName())
                .partyName(candidate.getJdName())
                .candidateImageUrl(null)
                .gender(candidate.getGender())
                .age(candidate.getAge())
                .edu(candidate.getEdu())
                .job(candidate.getJob())
                .career1(candidate.getCareer1())
                .career2(candidate.getCareer2())
                .sggName(candidate.getSggName())
                .sdName(candidate.getSdName())
                .giho(candidate.getGiho())
                .status(candidate.getStatus())
                .candidateType(candidate.getCandidateType())
                .manifestoSummary(null) // LLM 요약 미구현
                .manifestoItems(manifestoItems)
                .build();
    }

    // ──────────────────────────────────────────
    // 5. Map
    // ──────────────────────────────────────────

    public ElectionMapResponse getMap(String electionId, Integer depth, String regionCode, String viewMode) {
        Integer sgTypecode = 3; // 기본: 시도지사
        List<ElectionMapResponse.RegionItem> regions;

        if (depth == null || depth <= 1) {
            // depth=1: 시도 목록 + 시도별 후보자 수
            var sdNames = districtRepository.findDistinctSdNameBySgIdAndSgTypecode(electionId, sgTypecode);
            var countMap = candidateRepository.countBySdNameAndSgIdAndSgTypecode(electionId, sgTypecode)
                    .stream()
                    .collect(Collectors.toMap(r -> (String) r[0], r -> ((Number) r[1]).intValue()));

            regions = sdNames.stream()
                    .map(sd -> ElectionMapResponse.RegionItem.builder()
                            .regionCode(sd)
                            .regionName(sd)
                            .value(countMap.getOrDefault(sd, 0))
                            .build())
                    .toList();
        } else {
            // depth=2: 특정 시도 하위 선거구
            var districts = districtRepository.findBySgIdAndSgTypecodeAndSdName(
                    electionId, sgTypecode, regionCode != null ? regionCode : "");
            regions = districts.stream()
                    .map(d -> ElectionMapResponse.RegionItem.builder()
                            .regionCode(d.getSggName())
                            .regionName(d.getSggName())
                            .value(d.getSggJungsu())
                            .build())
                    .toList();
        }

        return ElectionMapResponse.builder()
                .selectedElectionId(electionId)
                .depth(depth != null ? depth : 1)
                .regionCode(regionCode)
                .viewMode(viewMode)
                .regions(regions)
                .build();
    }

    // ──────────────────────────────────────────
    // 6. Region Panel
    // ──────────────────────────────────────────

    public ElectionRegionPanelResponse getRegionPanel(
            String electionId, Integer depth, String regionCode, String officeType) {

        // 해당 지역의 선거종류별 후보자 수 집계
        var allCandidates = candidateRepository.findBySgIdAndSgTypecodeAndSdName(
                electionId, 3, regionCode != null ? regionCode : "");

        // 여러 선거종류(시도지사, 교육감 등)별 집계
        List<ElectionRegionPanelResponse.OfficeTypeSummary> officeTypes = new ArrayList<>();
        for (var entry : OFFICE_NAMES.entrySet()) {
            int tc = entry.getKey();
            if (tc == 0 || tc == 1 || tc == 2 || tc == 7) continue; // 지방선거 아닌 것 제외
            var count = candidateRepository.findBySgIdAndSgTypecodeAndSdName(
                    electionId, tc, regionCode != null ? regionCode : "").size();
            if (count > 0) {
                officeTypes.add(ElectionRegionPanelResponse.OfficeTypeSummary.builder()
                        .sgTypecode(tc)
                        .officeName(entry.getValue())
                        .candidateCount(count)
                        .build());
            }
        }

        int total = officeTypes.stream().mapToInt(ElectionRegionPanelResponse.OfficeTypeSummary::getCandidateCount).sum();

        return ElectionRegionPanelResponse.builder()
                .selectedElectionId(electionId)
                .regionCode(regionCode)
                .regionName(regionCode)
                .depth(depth != null ? depth : 1)
                .totalCandidates(total)
                .officeTypes(officeTypes)
                .build();
    }

    // ──────────────────────────────────────────
    // 7. Region Resolve / Confirm
    // ──────────────────────────────────────────

    public ElectionRegionResolveResponse resolveRegion(String electionId, String regionCode, String regionName) {
        // 지역 코드/이름이 주어지면 해당 지역으로 확인
        if (regionCode != null && !regionCode.isEmpty()) {
            return ElectionRegionResolveResponse.builder()
                    .electionId(electionId)
                    .state("gps-suggested")
                    .confirmationRequired(true)
                    .suggestedRegionType("PROVINCE")
                    .suggestedRegionCode(regionCode)
                    .suggestedRegionName(regionName != null ? regionName : regionCode)
                    .manualCorrectionAvailable(true)
                    .denyAvailable(true)
                    .build();
        }

        // 지역 정보 없으면 수동 입력 요청
        return ElectionRegionResolveResponse.builder()
                .electionId(electionId)
                .state("manual-required")
                .confirmationRequired(false)
                .suggestedRegionType(null)
                .suggestedRegionCode(null)
                .suggestedRegionName(null)
                .manualCorrectionAvailable(true)
                .denyAvailable(false)
                .build();
    }

    public ElectionRegionResolveResponse confirmRegion(String electionId, String regionCode, String regionName) {
        return ElectionRegionResolveResponse.builder()
                .electionId(electionId)
                .state("confirmed")
                .confirmationRequired(false)
                .suggestedRegionType("PROVINCE")
                .suggestedRegionCode(regionCode)
                .suggestedRegionName(regionName != null ? regionName : regionCode)
                .manualCorrectionAvailable(true)
                .denyAvailable(false)
                .build();
    }

    // ──────────────────────────────────────────
    // Helpers
    // ──────────────────────────────────────────

    private Integer parseTypecode(String officeType) {
        return switch (officeType.toLowerCase()) {
            case "mayor", "시도지사", "3" -> 3;
            case "county_head", "구시군장", "4" -> 4;
            case "council", "시도의원", "5" -> 5;
            case "county_council", "구시군의회의원", "6" -> 6;
            case "superintendent", "교육감", "11" -> 11;
            default -> 3;
        };
    }
}
