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
    }

    @Test
    void normalizesPartyNamesWithIrregularSpaces() {
        assertThat(normalizationService.normalizePartyName("국민의 힘"))
                .isEqualTo("국민의힘");
        assertThat(normalizationService.normalizePartyName("조국 혁신당"))
                .isEqualTo("조국혁신당");
        assertThat(normalizationService.normalizePartyName("조국혁 신당"))
                .isEqualTo("조국혁신당");
    }

    @Test
    void normalizesCandidateAlias() {
        assertThat(normalizationService.normalizeCandidateName("김 동 연"))
                .isEqualTo("김동연");
    }
}
