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
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
class PollQueryServiceTest {

    @SpringBootConfiguration
    @EnableAutoConfiguration
    @EnableJpaRepositories(basePackageClasses = {
            PollSurveyRepository.class,
            PollQuestionRepository.class,
            PollOptionRepository.class
    })
    @EntityScan(basePackageClasses = {
            PollSurvey.class,
            PollQuestion.class,
            PollOption.class
    })
    static class TestJpaConfig {
    }

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private PollSurveyRepository pollSurveyRepository;

    @Autowired
    private PollQuestionRepository pollQuestionRepository;

    @Autowired
    private PollOptionRepository pollOptionRepository;

    private final PollQuestionClassifier classifier = new PollQuestionClassifier();
    private final PollNormalizationService normalizationService = new PollNormalizationService();

    @Test
    void loadsSurveyQuestionsAndOptionsForElectionAndRegion() {
        PollSurvey survey = PollSurvey.builder()
                .registrationNumber("서울-001")
                .electionType("지방선거")
                .region("서울특별시 전체")
                .electionName("제9회 전국동시지방선거")
                .pollster("한국갤럽")
                .sponsor("테스트의뢰기관")
                .surveyStartDate(LocalDate.of(2026, 4, 1))
                .surveyEndDate(LocalDate.of(2026, 4, 2))
                .sampleSize(1000)
                .marginOfError("95% 신뢰수준 ±3.1%p")
                .sourceUrl("https://example.com/poll/1")
                .pdfPath("/tmp/poll-1.pdf")
                .build();
        entityManager.persist(survey);

        PollQuestion question = PollQuestion.builder()
                .registrationNumber(survey.getRegistrationNumber())
                .questionNumber(1)
                .questionTitle("서울시장 후보 지지율")
                .nCompleted(1000)
                .nWeighted(1000)
                .build();
        entityManager.persist(question);
        entityManager.flush();

        PollOption firstOption = PollOption.builder()
                .questionId(question.getQuestionId())
                .optionName("김후보")
                .percentage(new BigDecimal("45.50"))
                .build();
        PollOption secondOption = PollOption.builder()
                .questionId(question.getQuestionId())
                .optionName("이후보")
                .percentage(new BigDecimal("39.20"))
                .build();
        entityManager.persist(firstOption);
        entityManager.persist(secondOption);
        entityManager.flush();

        List<PollSurvey> surveys = pollSurveyRepository.findByElectionTypeAndRegionOrderBySurveyEndDateDesc(
                "지방선거",
                "서울특별시 전체"
        );
        List<PollQuestion> questions = pollQuestionRepository.findByRegistrationNumberOrderByQuestionNumberAsc(
                survey.getRegistrationNumber()
        );
        List<PollOption> options = pollOptionRepository.findByQuestionIdOrderByOptionIdAsc(question.getQuestionId());

        assertThat(surveys).hasSize(1);
        assertThat(surveys.get(0).getRegistrationNumber()).isEqualTo("서울-001");

        assertThat(questions).hasSize(1);
        assertThat(questions.get(0).getQuestionTitle()).isEqualTo("서울시장 후보 지지율");

        assertThat(options)
                .extracting(PollOption::getOptionName)
                .containsExactly("김후보", "이후보");
    }

    @Test
    void buildsOverviewAndAggregatesUndecidedOptions() {
        PollSurvey earlierSurvey = PollSurvey.builder()
                .registrationNumber("서울-001")
                .electionType("제9회 전국동시지방선거")
                .region("서울특별시 전체")
                .electionName("제9회 전국동시지방선거")
                .pollster("한국갤럽")
                .sponsor("테스트의뢰기관")
                .surveyStartDate(LocalDate.of(2026, 3, 25))
                .surveyEndDate(LocalDate.of(2026, 3, 26))
                .sampleSize(1000)
                .marginOfError("95% 신뢰수준 ±3.1%p")
                .sourceUrl("https://example.com/poll/1")
                .pdfPath("/tmp/poll-1.pdf")
                .build();
        PollSurvey latestSurvey = PollSurvey.builder()
                .registrationNumber("서울-002")
                .electionType("제9회 전국동시지방선거")
                .region("서울특별시 전체")
                .electionName("제9회 전국동시지방선거")
                .pollster("한국리서치")
                .sponsor("테스트의뢰기관")
                .surveyStartDate(LocalDate.of(2026, 4, 1))
                .surveyEndDate(LocalDate.of(2026, 4, 2))
                .sampleSize(1000)
                .marginOfError("95% 신뢰수준 ±3.1%p")
                .sourceUrl("https://example.com/poll/2")
                .pdfPath("/tmp/poll-2.pdf")
                .build();
        entityManager.persist(earlierSurvey);
        entityManager.persist(latestSurvey);

        Long earlierQuestionId = persistPartySupportQuestion(earlierSurvey.getRegistrationNumber(), "정당지지도");
        Long latestQuestionId = persistPartySupportQuestion(latestSurvey.getRegistrationNumber(), "정당 지지도");

        persistOption(earlierQuestionId, "더불어 민주당", "38.00");
        persistOption(earlierQuestionId, "국민의힘", "34.00");
        persistOption(earlierQuestionId, "없음", "12.00");
        persistOption(earlierQuestionId, "잘모름", "4.00");

        persistOption(latestQuestionId, "더불어 민주당", "42.50");
        persistOption(latestQuestionId, "국민의힘", "36.20");
        persistOption(latestQuestionId, "지지정당 없음", "9.30");
        persistOption(latestQuestionId, "모름", "5.10");
        persistOption(latestQuestionId, "무응답", "1.20");

        entityManager.flush();

        PollQueryService pollQueryService = new PollQueryService(
                pollSurveyRepository,
                pollQuestionRepository,
                pollOptionRepository,
                classifier,
                normalizationService
        );

        var response = pollQueryService.getOverview("local-2026", "11");

        assertThat(response.getLeadingParty().getPartyName()).isEqualTo("더불어민주당");
        assertThat(response.getLeadingParty().getPercentage()).isEqualByComparingTo("42.50");
        assertThat(response.getLeadingParty().getUndecided()).isEqualByComparingTo("15.60");

        assertThat(response.getPartyTrend()).hasSize(2);
        assertThat(response.getPartyTrend())
                .extracting(trend -> trend.getSurvey().getRegistrationNumber())
                .containsExactly("서울-001", "서울-002");

        assertThat(response.getLatestSurveys()).hasSize(2);
        assertThat(response.getLatestSurveys().get(0).getRegistrationNumber()).isEqualTo("서울-002");
        assertThat(response.getLatestSurveys().get(0).getSponsor()).isEqualTo("테스트의뢰기관");
        assertThat(response.getLatestSurveys().get(0).getSampleSize()).isEqualTo(1000);
        assertThat(response.getLatestSurveys().get(0).getMarginOfError()).isEqualTo("95% 신뢰수준 ±3.1%p");
        assertThat(response.getLatestSurveys().get(0).getQuestionTitle()).isEqualTo("정당 지지도");

        java.util.Optional<ElectionPollOverviewResponse.PartySnapshot> undecided = response.getLatestSurveys().get(0)
                .getSnapshot()
                .stream()
                .filter(option -> option.getPartyName().equals("undecided"))
                .findFirst();
        assertThat(undecided).isPresent();
        assertThat(response.getLatestSurveys().get(0).getSnapshot())
                .extracting(snapshot -> snapshot.getPartyName())
                .contains("더불어민주당", "국민의힘", "undecided");
        assertThat(response.getLatestSurveys().get(0).getSnapshot().stream()
                .filter(snapshot -> snapshot.getPartyName().equals("undecided"))
                .findFirst()
                .orElseThrow()
                .getPercentage()).isEqualByComparingTo("15.60");
    }

    @Test
    void buildsPartyResponseWithTrendSeriesAndRegionalDistribution() {
        persistSurvey("서울-101", "제9회 전국동시지방선거", "서울특별시 전체", "한국갤럽", LocalDate.of(2026, 3, 20));
        persistSurvey("서울-102", "제9회 전국동시지방선거", "서울특별시 전체", "한국리서치", LocalDate.of(2026, 4, 2));
        persistSurvey("경기-201", "제9회 전국동시지방선거", "경기도 전체", "넥스트리서치", LocalDate.of(2026, 4, 1));

        Long seoulOldQuestion = persistQuestion("서울-101", 1, "정당지지도");
        Long seoulLatestQuestion = persistQuestion("서울-102", 1, "정당지지도");
        Long gyeonggiQuestion = persistQuestion("경기-201", 1, "정당지지도");

        persistOption(seoulOldQuestion, "더불어 민주당", "37.00");
        persistOption(seoulOldQuestion, "국민의힘", "35.00");

        persistOption(seoulLatestQuestion, "더불어 민주당", "42.50");
        persistOption(seoulLatestQuestion, "국민의힘", "36.20");

        persistOption(gyeonggiQuestion, "더불어 민주당", "48.30");
        persistOption(gyeonggiQuestion, "국민의힘", "31.00");

        entityManager.flush();

        PollQueryService pollQueryService = new PollQueryService(
                pollSurveyRepository,
                pollQuestionRepository,
                pollOptionRepository,
                classifier,
                normalizationService
        );

        ElectionPollPartyResponse response = pollQueryService.getParty("local-2026", "더불어민주당");

        assertThat(response.getSelectedParty()).isEqualTo("더불어민주당");
        assertThat(response.getTrendSeries()).hasSize(3);
        assertThat(response.getTrendSeries())
                .extracting(point -> point.getSurvey().getRegistrationNumber())
                .containsExactly("서울-101", "경기-201", "서울-102");
        assertThat(response.getRegionalDistribution()).hasSize(2);
        assertThat(response.getRegionalDistribution())
                .extracting(ElectionPollPartyResponse.RegionalDistributionItem::getRegionName)
                .containsExactly("경기도 전체", "서울특별시 전체");
    }

    @Test
    void buildsRegionResponseWithPartySnapshotCandidateSnapshotAndLatestSurveys() {
        persistSurvey("서울-301", "제9회 전국동시지방선거", "서울특별시 전체", "한국갤럽", LocalDate.of(2026, 4, 1));
        persistSurvey("서울-302", "제9회 전국동시지방선거", "서울특별시 전체", "한국리서치", LocalDate.of(2026, 4, 2));

        Long partyQuestion = persistQuestion("서울-302", 1, "정당지지도");
        Long matchupQuestion = persistQuestion("서울-302", 2, "가상대결 - 김동연 vs 양향자");

        persistOption(partyQuestion, "더불어 민주당", "42.50");
        persistOption(partyQuestion, "국민의힘", "36.20");
        persistOption(partyQuestion, "모름", "5.10");

        persistOption(matchupQuestion, "김동연", "45.10");
        persistOption(matchupQuestion, "양향자", "39.20");
        persistOption(matchupQuestion, "없음", "10.00");

        entityManager.flush();

        PollQueryService pollQueryService = new PollQueryService(
                pollSurveyRepository,
                pollQuestionRepository,
                pollOptionRepository,
                classifier,
                normalizationService
        );

        ElectionPollRegionResponse response = pollQueryService.getRegion("local-2026", "11");

        assertThat(response.getRegionName()).isEqualTo("서울특별시 전체");
        assertThat(response.getPartySnapshot())
                .extracting(ElectionPollRegionResponse.PartySnapshot::getPartyName)
                .contains("더불어민주당", "국민의힘", "undecided");
        assertThat(response.getCandidateSnapshot())
                .extracting(ElectionPollRegionResponse.CandidateSnapshot::getCandidateName)
                .contains("김동연", "양향자", "undecided");
        assertThat(response.getLatestSurveys()).hasSize(2);
        assertThat(response.getLatestSurveys().get(0).getRegistrationNumber()).isEqualTo("서울-302");
        assertThat(response.getLatestSurveys().get(0).getSponsor()).isEqualTo("테스트의뢰기관");
        assertThat(response.getLatestSurveys().get(0).getSampleSize()).isEqualTo(1000);
        assertThat(response.getLatestSurveys().get(0).getQuestionTitle()).isEqualTo("정당지지도");
    }

    @Test
    void prefersMatchupForCandidateResponse() {
        persistSurvey("서울-401", "제9회 전국동시지방선거", "서울특별시 전체", "한국리서치", LocalDate.of(2026, 4, 2));

        Long fitQuestion = persistQuestion("서울-401", 1, "서울시장 후보 적합도");
        Long matchupQuestion = persistQuestion("서울-401", 2, "가상대결 - 김동연 vs 양향자");

        persistOption(fitQuestion, "김동연", "41.00");
        persistOption(fitQuestion, "양향자", "35.00");

        persistOption(matchupQuestion, "김동연", "45.10");
        persistOption(matchupQuestion, "양향자", "39.20");
        persistOption(matchupQuestion, "모름", "5.70");

        entityManager.flush();

        PollQueryService pollQueryService = new PollQueryService(
                pollSurveyRepository,
                pollQuestionRepository,
                pollOptionRepository,
                classifier,
                normalizationService
        );

        ElectionPollCandidateResponse response = pollQueryService.getCandidate("local-2026", "11", "김동연");

        assertThat(response.getBasisQuestionKind()).isEqualTo("MATCHUP");
        assertThat(response.getSelectedCandidate()).isEqualTo("김동연");
        assertThat(response.getCandidateOptions()).containsExactly("김동연", "양향자");
    }

    @Test
    void fallsBackToCandidateFitWhenMatchupIsMissing() {
        persistSurvey("경기-501", "제9회 전국동시지방선거", "경기도 전체", "넥스트리서치", LocalDate.of(2026, 4, 3));

        Long fitQuestion = persistQuestion("경기-501", 1, "경기도지사 진보 후보 적합도");

        persistOption(fitQuestion, "김 동 연", "44.20");
        persistOption(fitQuestion, "김후보", "31.00");
        persistOption(fitQuestion, "없음", "7.00");

        entityManager.flush();

        PollQueryService pollQueryService = new PollQueryService(
                pollSurveyRepository,
                pollQuestionRepository,
                pollOptionRepository,
                classifier,
                normalizationService
        );

        ElectionPollCandidateResponse response = pollQueryService.getCandidate("local-2026", "41", "김동연");

        assertThat(response.getBasisQuestionKind()).isEqualTo("CANDIDATE_FIT");
        assertThat(response.getSelectedCandidate()).isEqualTo("김동연");
        assertThat(response.getCandidateOptions()).contains("김동연", "김후보");
    }

    private void persistSurvey(
            String registrationNumber,
            String electionType,
            String region,
            String pollster,
            LocalDate surveyEndDate
    ) {
        entityManager.persist(PollSurvey.builder()
                .registrationNumber(registrationNumber)
                .electionType(electionType)
                .region(region)
                .electionName(electionType)
                .pollster(pollster)
                .sponsor("테스트의뢰기관")
                .surveyStartDate(surveyEndDate.minusDays(1))
                .surveyEndDate(surveyEndDate)
                .sampleSize(1000)
                .marginOfError("95% 신뢰수준 ±3.1%p")
                .sourceUrl("https://example.com/" + registrationNumber)
                .pdfPath("/tmp/" + registrationNumber + ".pdf")
                .build());
    }

    private Long persistPartySupportQuestion(String registrationNumber, String title) {
        return persistQuestion(registrationNumber, 1, title);
    }

    private Long persistQuestion(String registrationNumber, int questionNumber, String title) {
        PollQuestion question = PollQuestion.builder()
                .registrationNumber(registrationNumber)
                .questionNumber(questionNumber)
                .questionTitle(title)
                .nCompleted(1000)
                .nWeighted(1000)
                .build();
        entityManager.persist(question);
        entityManager.flush();
        return question.getQuestionId();
    }

    private void persistOption(Long questionId, String optionName, String percentage) {
        entityManager.persist(PollOption.builder()
                .questionId(questionId)
                .optionName(optionName)
                .percentage(new BigDecimal(percentage))
                .build());
    }
}
