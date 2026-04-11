package com.everyones.lawmaking.service.election.poll;

import com.everyones.lawmaking.common.dto.response.election.ElectionPollOverviewResponse;
import com.everyones.lawmaking.domain.entity.poll.PollOption;
import com.everyones.lawmaking.domain.entity.poll.PollQuestion;
import com.everyones.lawmaking.domain.entity.poll.PollSurvey;
import com.everyones.lawmaking.repository.poll.PollOptionRepository;
import com.everyones.lawmaking.repository.poll.PollQuestionRepository;
import com.everyones.lawmaking.repository.poll.PollSurveyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PollQueryService {

    private static final String UNDECIDED = "undecided";
    private static final List<String> UNDECIDED_KEYWORDS = List.of(
            "없음",
            "없다",
            "없음/모름",
            "지지정당없음",
            "무응답",
            "모름",
            "잘모름",
            "의견유보",
            "기타"
    );

    private final PollSurveyRepository pollSurveyRepository;
    private final PollQuestionRepository pollQuestionRepository;
    private final PollOptionRepository pollOptionRepository;
    private final PollQuestionClassifier pollQuestionClassifier;
    private final PollNormalizationService pollNormalizationService;

    public ElectionPollOverviewResponse getOverview(String electionId, String regionCode) {
        String electionLabel = pollNormalizationService.normalizeElectionLabel(electionId);
        String regionLabel = pollNormalizationService.normalizeRegionLabel(regionCode, null);

        List<SurveySnapshot> snapshots = pollSurveyRepository
                .findByElectionTypeAndRegionOrderBySurveyEndDateDesc(electionLabel, regionLabel)
                .stream()
                .map(this::toSurveySnapshot)
                .flatMap(Optional::stream)
                .toList();

        List<ElectionPollOverviewResponse.LatestSurveyResponse> latestSurveys = snapshots.stream()
                .map(this::toLatestSurveyResponse)
                .toList();

        List<ElectionPollOverviewResponse.PartyTrendPoint> partyTrend = snapshots.stream()
                .sorted(Comparator.comparing(SurveySnapshot::surveyEndDate, Comparator.nullsLast(Comparator.naturalOrder())))
                .map(this::toTrendPoint)
                .toList();

        return ElectionPollOverviewResponse.builder()
                .leadingParty(buildLeadingParty(latestSurveys))
                .partyTrend(partyTrend)
                .latestSurveys(latestSurveys)
                .build();
    }

    private Optional<SurveySnapshot> toSurveySnapshot(PollSurvey survey) {
        return pollQuestionRepository.findByRegistrationNumberOrderByQuestionNumberAsc(survey.getRegistrationNumber())
                .stream()
                .filter(question -> pollQuestionClassifier.classify(question.getQuestionTitle(), null)
                        == PollQuestionClassifier.QuestionType.PARTY_SUPPORT)
                .findFirst()
                .map(question -> buildSurveySnapshot(survey, question));
    }

    private SurveySnapshot buildSurveySnapshot(PollSurvey survey, PollQuestion question) {
        Map<String, BigDecimal> aggregated = new LinkedHashMap<>();
        BigDecimal undecided = BigDecimal.ZERO;

        for (PollOption option : pollOptionRepository.findByQuestionIdOrderByOptionIdAsc(question.getQuestionId())) {
            BigDecimal percentage = option.getPercentage() == null ? BigDecimal.ZERO : option.getPercentage();
            if (isUndecidedOption(option.getOptionName())) {
                undecided = undecided.add(percentage);
                continue;
            }

            String normalizedParty = pollNormalizationService.normalizePartyName(option.getOptionName());
            aggregated.merge(normalizedParty, percentage, BigDecimal::add);
        }

        if (undecided.compareTo(BigDecimal.ZERO) > 0) {
            aggregated.put(UNDECIDED, undecided);
        }

        List<ElectionPollOverviewResponse.PartySnapshot> snapshot = aggregated.entrySet().stream()
                .map(entry -> ElectionPollOverviewResponse.PartySnapshot.builder()
                        .partyName(entry.getKey())
                        .percentage(entry.getValue())
                        .build())
                .sorted(Comparator.comparing(ElectionPollOverviewResponse.PartySnapshot::getPercentage).reversed())
                .toList();

        return new SurveySnapshot(
                survey.getRegistrationNumber(),
                survey.getPollster(),
                survey.getSurveyEndDate(),
                snapshot
        );
    }

    private ElectionPollOverviewResponse.LeadingPartyResponse buildLeadingParty(
            List<ElectionPollOverviewResponse.LatestSurveyResponse> latestSurveys
    ) {
        if (latestSurveys.isEmpty()) {
            return null;
        }

        List<ElectionPollOverviewResponse.PartySnapshot> latestSnapshot = latestSurveys.get(0).getSnapshot();
        List<ElectionPollOverviewResponse.PartySnapshot> majorParties = latestSnapshot.stream()
                .filter(snapshot -> !UNDECIDED.equals(snapshot.getPartyName()))
                .toList();

        if (majorParties.isEmpty()) {
            return null;
        }

        ElectionPollOverviewResponse.PartySnapshot leading = majorParties.get(0);
        ElectionPollOverviewResponse.PartySnapshot runnerUp = majorParties.size() > 1 ? majorParties.get(1) : null;
        BigDecimal undecided = latestSnapshot.stream()
                .filter(snapshot -> UNDECIDED.equals(snapshot.getPartyName()))
                .map(ElectionPollOverviewResponse.PartySnapshot::getPercentage)
                .findFirst()
                .orElse(BigDecimal.ZERO);

        return ElectionPollOverviewResponse.LeadingPartyResponse.builder()
                .partyName(leading.getPartyName())
                .percentage(leading.getPercentage())
                .runnerUpParty(runnerUp == null ? null : runnerUp.getPartyName())
                .gap(runnerUp == null ? BigDecimal.ZERO : leading.getPercentage().subtract(runnerUp.getPercentage()))
                .undecided(undecided)
                .build();
    }

    private ElectionPollOverviewResponse.PartyTrendPoint toTrendPoint(SurveySnapshot snapshot) {
        return ElectionPollOverviewResponse.PartyTrendPoint.builder()
                .survey(ElectionPollOverviewResponse.SurveyReference.builder()
                        .registrationNumber(snapshot.registrationNumber())
                        .pollster(snapshot.pollster())
                        .surveyEndDate(snapshot.surveyEndDate())
                        .build())
                .snapshot(snapshot.snapshot())
                .build();
    }

    private ElectionPollOverviewResponse.LatestSurveyResponse toLatestSurveyResponse(SurveySnapshot snapshot) {
        return ElectionPollOverviewResponse.LatestSurveyResponse.builder()
                .registrationNumber(snapshot.registrationNumber())
                .pollster(snapshot.pollster())
                .surveyEndDate(snapshot.surveyEndDate())
                .snapshot(snapshot.snapshot())
                .build();
    }

    private boolean isUndecidedOption(String optionName) {
        String normalized = optionName == null ? "" : optionName.replaceAll("\\s+", "");
        for (String keyword : UNDECIDED_KEYWORDS) {
            if (normalized.contains(keyword.replaceAll("\\s+", ""))) {
                return true;
            }
        }
        return false;
    }

    private record SurveySnapshot(
            String registrationNumber,
            String pollster,
            LocalDate surveyEndDate,
            List<ElectionPollOverviewResponse.PartySnapshot> snapshot
    ) {
    }
}
