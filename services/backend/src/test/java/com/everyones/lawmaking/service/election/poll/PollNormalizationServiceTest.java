package com.everyones.lawmaking.service.election.poll;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class PollNormalizationServiceTest {

    private final PollNormalizationService normalizationService = new PollNormalizationService();

    @Test
    void mapsRegionCodeAndNameToPollRegionLabel() {
        assertThat(normalizationService.normalizeRegionLabel("11", "서울특별시"))
                .isEqualTo("서울특별시 전체");
    }

    @Test
    void mapsElectionIdToPollElectionLabel() {
        assertThat(normalizationService.normalizeElectionLabel("local-2026"))
                .isEqualTo("제9회 전국동시지방선거");
    }

    @Test
    void mapsRealElectionIdToPollElectionLabel() {
        assertThat(normalizationService.normalizeElectionLabel("20260603"))
                .isEqualTo("제9회 전국동시지방선거");
    }

    @Test
    void normalizesPartyAlias() {
        assertThat(normalizationService.normalizePartyName("더불어 민주당"))
                .isEqualTo("더불어민주당");
        assertThat(normalizationService.normalizePartyName("국민의 힘"))
                .isEqualTo("국민의힘");
        assertThat(normalizationService.normalizePartyName("개혁 신당"))
                .isEqualTo("개혁신당");
        assertThat(normalizationService.normalizePartyName("조국 혁신당"))
                .isEqualTo("조국혁신당");
    }

    @Test
    void normalizesCandidateAlias() {
        assertThat(normalizationService.normalizeCandidateName("김 동 연"))
                .isEqualTo("김동연");
        assertThat(normalizationService.normalizeCandidateName("잘 모르겠다"))
                .isEqualTo("undecided");
    }

    @Test
    void identifiesPlaceholderQuestionTitle() {
        assertThat(normalizationService.isMeaningfulQuestionTitle("Q7")).isFalse();
        assertThat(normalizationService.isMeaningfulQuestionTitle("")).isFalse();
        assertThat(normalizationService.isMeaningfulQuestionTitle("정당지지도")).isTrue();
    }

    @Test
    void identifiesSuspiciousPartyOption() {
        assertThat(normalizationService.isSuspiciousPartyOption("선택지1")).isTrue();
        assertThat(normalizationService.isSuspiciousPartyOption("민주당국민의힘")).isTrue();
        assertThat(normalizationService.isSuspiciousPartyOption("더불어민주당")).isFalse();
    }

    @Test
    void identifiesCorruptedText() {
        assertThat(normalizationService.looksCorruptedText("먚鰃믅믅鱮 (1)")).isTrue();
        assertThat(normalizationService.looksCorruptedText("서울시장 더불어민주당 후보 적합도")).isFalse();
    }
}
