package com.everyones.lawmaking.service.election.poll;

import com.everyones.lawmaking.common.dto.response.election.ElectionPollCandidateResponse;
import com.everyones.lawmaking.common.dto.response.election.ElectionPollOverviewResponse;
import com.everyones.lawmaking.common.dto.response.election.ElectionPollPartyResponse;
import com.everyones.lawmaking.common.dto.response.election.ElectionPollRegionResponse;
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
            "그외정당",
            "그외다른정당",
            "무응답",
            "모름",
            "잘모르겠다",
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

        List<PartySurveySnapshot> snapshots = pollSurveyRepository
                .findByElectionTypeAndRegionOrderBySurveyEndDateDesc(electionLabel, regionLabel)
                .stream()
                .map(this::toPartySurveySnapshot)
                .flatMap(Optional::stream)
                .toList();

        List<ElectionPollOverviewResponse.LatestSurveyResponse> latestSurveys = snapshots.stream()
                .map(this::toOverviewLatestSurveyResponse)
                .toList();

        List<ElectionPollOverviewResponse.PartyTrendPoint> partyTrend = snapshots.stream()
                .sorted(Comparator.comparing(PartySurveySnapshot::surveyEndDate, Comparator.nullsLast(Comparator.naturalOrder())))
                .map(this::toOverviewTrendPoint)
                .toList();

        return ElectionPollOverviewResponse.builder()
                .leadingParty(buildLeadingParty(latestSurveys))
                .partyTrend(partyTrend)
                .latestSurveys(latestSurveys)
                .build();
    }

    public ElectionPollPartyResponse getParty(String electionId, String partyName) {
        String electionLabel = pollNormalizationService.normalizeElectionLabel(electionId);
        String normalizedParty = pollNormalizationService.normalizePartyName(partyName);

        List<PartySurveySnapshot> snapshots = pollSurveyRepository.findByElectionTypeOrderBySurveyEndDateDesc(electionLabel)
                .stream()
                .map(this::toPartySurveySnapshot)
                .flatMap(Optional::stream)
                .filter(snapshot -> snapshot.findPercentage(normalizedParty).isPresent())
                .toList();

        List<ElectionPollPartyResponse.TrendPoint> trendSeries = snapshots.stream()
                .sorted(Comparator.comparing(PartySurveySnapshot::surveyEndDate, Comparator.nullsLast(Comparator.naturalOrder())))
                .map(snapshot -> ElectionPollPartyResponse.TrendPoint.builder()
                        .survey(toPartySurveyReference(snapshot))
                        .percentage(snapshot.findPercentage(normalizedParty).orElse(BigDecimal.ZERO))
                        .build())
                .toList();

        Map<String, PartySurveySnapshot> latestByRegion = new LinkedHashMap<>();
        for (PartySurveySnapshot snapshot : snapshots) {
            latestByRegion.putIfAbsent(snapshot.regionName(), snapshot);
        }

        List<ElectionPollPartyResponse.RegionalDistributionItem> regionalDistribution = latestByRegion.values().stream()
                .map(snapshot -> ElectionPollPartyResponse.RegionalDistributionItem.builder()
                        .regionName(snapshot.regionName())
                        .percentage(snapshot.findPercentage(normalizedParty).orElse(BigDecimal.ZERO))
                        .build())
                .sorted(Comparator.comparing(ElectionPollPartyResponse.RegionalDistributionItem::getPercentage).reversed())
                .toList();

        return ElectionPollPartyResponse.builder()
                .selectedParty(normalizedParty)
                .trendSeries(trendSeries)
                .regionalDistribution(regionalDistribution)
                .build();
    }

    public ElectionPollRegionResponse getRegion(String electionId, String regionCode) {
        String electionLabel = pollNormalizationService.normalizeElectionLabel(electionId);
        String regionLabel = pollNormalizationService.normalizeRegionLabel(regionCode, null);

        List<PollSurvey> surveys = pollSurveyRepository.findByElectionTypeAndRegionOrderBySurveyEndDateDesc(electionLabel, regionLabel);
        List<PartySurveySnapshot> partySnapshots = surveys.stream()
                .map(this::toPartySurveySnapshot)
                .flatMap(Optional::stream)
                .toList();

        List<CandidateSurveySnapshot> matchupSnapshots = getCandidateSnapshots(surveys, PollQuestionClassifier.QuestionType.MATCHUP);
        List<CandidateSurveySnapshot> fitSnapshots = getCandidateSnapshots(surveys, PollQuestionClassifier.QuestionType.CANDIDATE_FIT);
        List<CandidateSurveySnapshot> preferredCandidateSnapshots = !matchupSnapshots.isEmpty() ? matchupSnapshots : fitSnapshots;

        List<ElectionPollRegionResponse.SurveySummary> latestSurveys = surveys.stream()
                .map(this::toRegionSurveySummary)
                .toList();

        List<ElectionPollRegionResponse.PartySnapshot> partySnapshot = partySnapshots.isEmpty()
                ? List.of()
                : partySnapshots.get(0).snapshot().stream()
                .map(snapshot -> ElectionPollRegionResponse.PartySnapshot.builder()
                        .partyName(snapshot.getPartyName())
                        .percentage(snapshot.getPercentage())
                        .build())
                .toList();

        List<ElectionPollRegionResponse.CandidateSnapshot> candidateSnapshot = preferredCandidateSnapshots.isEmpty()
                ? List.of()
                : preferredCandidateSnapshots.get(0).snapshot().stream()
                .map(snapshot -> ElectionPollRegionResponse.CandidateSnapshot.builder()
                        .candidateName(snapshot.getCandidateName())
                        .percentage(snapshot.getPercentage())
                        .build())
                .toList();

        return ElectionPollRegionResponse.builder()
                .regionName(regionLabel)
                .partySnapshot(partySnapshot)
                .candidateSnapshot(candidateSnapshot)
                .latestSurveys(latestSurveys)
                .build();
    }

    public ElectionPollCandidateResponse getCandidate(String electionId, String regionCode, String candidateName) {
        String electionLabel = pollNormalizationService.normalizeElectionLabel(electionId);
        String regionLabel = pollNormalizationService.normalizeRegionLabel(regionCode, null);

        List<PollSurvey> surveys = pollSurveyRepository.findByElectionTypeAndRegionOrderBySurveyEndDateDesc(electionLabel, regionLabel);
        List<CandidateSurveySnapshot> matchupSnapshots = getCandidateSnapshots(surveys, PollQuestionClassifier.QuestionType.MATCHUP);
        List<CandidateSurveySnapshot> fitSnapshots = getCandidateSnapshots(surveys, PollQuestionClassifier.QuestionType.CANDIDATE_FIT);

        boolean useMatchup = !matchupSnapshots.isEmpty();
        List<CandidateSurveySnapshot> selectedSnapshots = useMatchup ? matchupSnapshots : fitSnapshots;

        if (selectedSnapshots.isEmpty()) {
            return ElectionPollCandidateResponse.builder()
                    .selectedCandidate(pollNormalizationService.normalizeCandidateName(candidateName))
                    .basisQuestionKind(null)
                    .candidateOptions(List.of())
                    .series(List.of())
                    .comparisonSeries(List.of())
                    .latestSnapshot(List.of())
                    .build();
        }

        List<ElectionPollCandidateResponse.CandidateSnapshot> latestSnapshot = selectedSnapshots.get(0).snapshot();
        List<String> candidateOptions = latestSnapshot.stream()
                .filter(snapshot -> !UNDECIDED.equals(snapshot.getCandidateName()))
                .map(ElectionPollCandidateResponse.CandidateSnapshot::getCandidateName)
                .toList();

        String normalizedCandidate = pollNormalizationService.normalizeCandidateName(candidateName);
        String selectedCandidate = candidateOptions.contains(normalizedCandidate)
                ? normalizedCandidate
                : candidateOptions.get(0);

        List<CandidateSurveySnapshot> orderedSnapshots = selectedSnapshots.stream()
                .sorted(Comparator.comparing(CandidateSurveySnapshot::surveyEndDate, Comparator.nullsLast(Comparator.naturalOrder())))
                .toList();

        List<ElectionPollCandidateResponse.CandidateTrendPoint> series = buildCandidateTrendSeries(orderedSnapshots, selectedCandidate);
        List<ElectionPollCandidateResponse.CandidateSeries> comparisonSeries = candidateOptions.stream()
                .filter(option -> !option.equals(selectedCandidate))
                .map(option -> ElectionPollCandidateResponse.CandidateSeries.builder()
                        .candidateName(option)
                        .series(buildCandidateTrendSeries(orderedSnapshots, option))
                        .build())
                .toList();

        return ElectionPollCandidateResponse.builder()
                .selectedCandidate(selectedCandidate)
                .basisQuestionKind(useMatchup ? PollQuestionClassifier.QuestionType.MATCHUP.name() : PollQuestionClassifier.QuestionType.CANDIDATE_FIT.name())
                .candidateOptions(candidateOptions)
                .series(series)
                .comparisonSeries(comparisonSeries)
                .latestSnapshot(latestSnapshot)
                .build();
    }

    private List<CandidateSurveySnapshot> getCandidateSnapshots(
            List<PollSurvey> surveys,
            PollQuestionClassifier.QuestionType questionType
    ) {
        return surveys.stream()
                .map(survey -> toCandidateSurveySnapshot(survey, questionType))
                .flatMap(Optional::stream)
                .toList();
    }

    private Optional<PartySurveySnapshot> toPartySurveySnapshot(PollSurvey survey) {
        return pollQuestionRepository.findByRegistrationNumberOrderByQuestionNumberAsc(survey.getRegistrationNumber())
                .stream()
                .filter(question -> pollQuestionClassifier.classify(question.getQuestionTitle(), null)
                        == PollQuestionClassifier.QuestionType.PARTY_SUPPORT)
                .findFirst()
                .map(question -> buildPartySurveySnapshot(survey, question));
    }

    private PartySurveySnapshot buildPartySurveySnapshot(PollSurvey survey, PollQuestion question) {
        Map<String, BigDecimal> aggregated = aggregateOptions(
                pollOptionRepository.findByQuestionIdOrderByOptionIdAsc(question.getQuestionId()),
                option -> pollNormalizationService.normalizePartyName(option.getOptionName())
        );

        List<ElectionPollOverviewResponse.PartySnapshot> snapshot = aggregated.entrySet().stream()
                .map(entry -> ElectionPollOverviewResponse.PartySnapshot.builder()
                        .partyName(entry.getKey())
                        .percentage(entry.getValue())
                        .build())
                .sorted(Comparator.comparing(ElectionPollOverviewResponse.PartySnapshot::getPercentage).reversed())
                .toList();

        return new PartySurveySnapshot(
                survey.getRegistrationNumber(),
                survey.getPollster(),
                survey.getSponsor(),
                survey.getSurveyEndDate(),
                survey.getSampleSize(),
                survey.getMarginOfError(),
                survey.getRegion(),
                question.getQuestionTitle(),
                snapshot
        );
    }

    private Optional<CandidateSurveySnapshot> toCandidateSurveySnapshot(
            PollSurvey survey,
            PollQuestionClassifier.QuestionType questionType
    ) {
        return pollQuestionRepository.findByRegistrationNumberOrderByQuestionNumberAsc(survey.getRegistrationNumber())
                .stream()
                .filter(question -> pollQuestionClassifier.classify(question.getQuestionTitle(), null) == questionType)
                .findFirst()
                .map(question -> buildCandidateSurveySnapshot(survey, question, questionType));
    }

    private CandidateSurveySnapshot buildCandidateSurveySnapshot(
            PollSurvey survey,
            PollQuestion question,
            PollQuestionClassifier.QuestionType questionType
    ) {
        Map<String, BigDecimal> aggregated = aggregateOptions(
                pollOptionRepository.findByQuestionIdOrderByOptionIdAsc(question.getQuestionId()),
                option -> pollNormalizationService.normalizeCandidateName(option.getOptionName())
        );

        List<ElectionPollCandidateResponse.CandidateSnapshot> snapshot = aggregated.entrySet().stream()
                .map(entry -> ElectionPollCandidateResponse.CandidateSnapshot.builder()
                        .candidateName(entry.getKey())
                        .percentage(entry.getValue())
                        .build())
                .sorted(Comparator.comparing(ElectionPollCandidateResponse.CandidateSnapshot::getPercentage).reversed())
                .toList();

        return new CandidateSurveySnapshot(
                survey.getRegistrationNumber(),
                survey.getPollster(),
                survey.getSurveyEndDate(),
                questionType,
                snapshot
        );
    }

    private Map<String, BigDecimal> aggregateOptions(
            List<PollOption> options,
            java.util.function.Function<PollOption, String> normalizer
    ) {
        Map<String, BigDecimal> aggregated = new LinkedHashMap<>();
        BigDecimal undecided = BigDecimal.ZERO;

        for (PollOption option : options) {
            BigDecimal percentage = option.getPercentage() == null ? BigDecimal.ZERO : option.getPercentage();
            if (isUndecidedOption(option.getOptionName())) {
                undecided = undecided.add(percentage);
                continue;
            }

            aggregated.merge(normalizer.apply(option), percentage, BigDecimal::add);
        }

        if (undecided.compareTo(BigDecimal.ZERO) > 0) {
            aggregated.put(UNDECIDED, undecided);
        }

        return aggregated;
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

    private ElectionPollOverviewResponse.PartyTrendPoint toOverviewTrendPoint(PartySurveySnapshot snapshot) {
        return ElectionPollOverviewResponse.PartyTrendPoint.builder()
                .survey(ElectionPollOverviewResponse.SurveyReference.builder()
                        .registrationNumber(snapshot.registrationNumber())
                        .pollster(snapshot.pollster())
                        .surveyEndDate(snapshot.surveyEndDate())
                        .build())
                .snapshot(snapshot.snapshot())
                .build();
    }

    private ElectionPollOverviewResponse.LatestSurveyResponse toOverviewLatestSurveyResponse(PartySurveySnapshot snapshot) {
        return ElectionPollOverviewResponse.LatestSurveyResponse.builder()
                .registrationNumber(snapshot.registrationNumber())
                .pollster(snapshot.pollster())
                .sponsor(snapshot.sponsor())
                .surveyEndDate(snapshot.surveyEndDate())
                .sampleSize(snapshot.sampleSize())
                .marginOfError(snapshot.marginOfError())
                .questionTitle(snapshot.questionTitle())
                .snapshot(snapshot.snapshot())
                .build();
    }

    private ElectionPollPartyResponse.SurveyReference toPartySurveyReference(PartySurveySnapshot snapshot) {
        return ElectionPollPartyResponse.SurveyReference.builder()
                .registrationNumber(snapshot.registrationNumber())
                .pollster(snapshot.pollster())
                .surveyEndDate(snapshot.surveyEndDate())
                .build();
    }

    private ElectionPollRegionResponse.SurveySummary toRegionSurveySummary(PollSurvey survey) {
        return ElectionPollRegionResponse.SurveySummary.builder()
                .registrationNumber(survey.getRegistrationNumber())
                .pollster(survey.getPollster())
                .sponsor(survey.getSponsor())
                .surveyEndDate(survey.getSurveyEndDate())
                .sampleSize(survey.getSampleSize())
                .marginOfError(survey.getMarginOfError())
                .questionTitle(resolveRepresentativeQuestionTitle(survey.getRegistrationNumber()))
                .build();
    }

    private String resolveRepresentativeQuestionTitle(String registrationNumber) {
        return pollQuestionRepository.findByRegistrationNumberOrderByQuestionNumberAsc(registrationNumber)
                .stream()
                .filter(question -> {
                    PollQuestionClassifier.QuestionType type = pollQuestionClassifier.classify(question.getQuestionTitle(), null);
                    return type == PollQuestionClassifier.QuestionType.PARTY_SUPPORT
                            || type == PollQuestionClassifier.QuestionType.MATCHUP
                            || type == PollQuestionClassifier.QuestionType.CANDIDATE_FIT;
                })
                .map(PollQuestion::getQuestionTitle)
                .findFirst()
                .orElse(null);
    }

    private List<ElectionPollCandidateResponse.CandidateTrendPoint> buildCandidateTrendSeries(
            List<CandidateSurveySnapshot> snapshots,
            String candidateName
    ) {
        return snapshots.stream()
                .map(snapshot -> snapshot.findPercentage(candidateName)
                        .map(percentage -> ElectionPollCandidateResponse.CandidateTrendPoint.builder()
                                .survey(ElectionPollCandidateResponse.SurveyReference.builder()
                                        .registrationNumber(snapshot.registrationNumber())
                                        .pollster(snapshot.pollster())
                                        .surveyEndDate(snapshot.surveyEndDate())
                                        .build())
                                .percentage(percentage)
                                .build()))
                .flatMap(Optional::stream)
                .toList();
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

    private record PartySurveySnapshot(
            String registrationNumber,
            String pollster,
            String sponsor,
            LocalDate surveyEndDate,
            Integer sampleSize,
            String marginOfError,
            String regionName,
            String questionTitle,
            List<ElectionPollOverviewResponse.PartySnapshot> snapshot
    ) {
        Optional<BigDecimal> findPercentage(String partyName) {
            return snapshot.stream()
                    .filter(item -> item.getPartyName().equals(partyName))
                    .map(ElectionPollOverviewResponse.PartySnapshot::getPercentage)
                    .findFirst();
        }
    }

    private record CandidateSurveySnapshot(
            String registrationNumber,
            String pollster,
            LocalDate surveyEndDate,
            PollQuestionClassifier.QuestionType questionType,
            List<ElectionPollCandidateResponse.CandidateSnapshot> snapshot
    ) {
        Optional<BigDecimal> findPercentage(String candidateName) {
            return snapshot.stream()
                    .filter(item -> item.getCandidateName().equals(candidateName))
                    .map(ElectionPollCandidateResponse.CandidateSnapshot::getPercentage)
                    .findFirst();
        }
    }
}
