package com.everyones.lawmaking.service.election.poll;

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
}
