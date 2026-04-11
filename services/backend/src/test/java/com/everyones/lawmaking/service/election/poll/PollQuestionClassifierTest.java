package com.everyones.lawmaking.service.election.poll;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class PollQuestionClassifierTest {

    private final PollQuestionClassifier classifier = new PollQuestionClassifier();

    @Test
    void classifiesPartySupportQuestion() {
        assertThat(classifier.classify("정당지지도", null))
                .isEqualTo(PollQuestionClassifier.QuestionType.PARTY_SUPPORT);
    }

    @Test
    void classifiesCandidateFitQuestion() {
        assertThat(classifier.classify("경기도지사 진보 후보 적합도", null))
                .isEqualTo(PollQuestionClassifier.QuestionType.CANDIDATE_FIT);
    }

    @Test
    void classifiesMatchupQuestion() {
        assertThat(classifier.classify("가상대결 A - 김동연 vs 양향자", null))
                .isEqualTo(PollQuestionClassifier.QuestionType.MATCHUP);
    }
}
