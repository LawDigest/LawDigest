package com.everyones.lawmaking.service.election;

import com.everyones.lawmaking.common.dto.response.election.ElectionCandidateListResponse;
import com.everyones.lawmaking.domain.entity.election.ElectionCandidate;
import com.everyones.lawmaking.repository.election.ElectionCandidateRepository;
import com.everyones.lawmaking.repository.election.ElectionCodeRepository;
import com.everyones.lawmaking.repository.election.ElectionDistrictRepository;
import com.everyones.lawmaking.repository.election.ElectionWinnerRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;

@ExtendWith(MockitoExtension.class)
class ElectionServiceTest {

    @Mock
    private ElectionCodeRepository electionCodeRepository;

    @Mock
    private ElectionCandidateRepository candidateRepository;

    @Mock
    private ElectionDistrictRepository districtRepository;

    @Mock
    private ElectionWinnerRepository winnerRepository;

    @InjectMocks
    private ElectionService electionService;

    @Test
    @DisplayName("확정후보가 있으면 예비후보 대신 확정후보 목록만 반환한다")
    void getCandidatesReturnsConfirmedCandidatesWhenPresent() {
        given(candidateRepository.findBySgIdAndSgTypecodeAndSdName("20260603", 3, "서울특별시"))
                .willReturn(List.of(
                        candidate(1L, "예비 후보", "PRELIMINARY"),
                        candidate(2L, "확정 후보", "CONFIRMED")
                ));

        ElectionCandidateListResponse response = electionService.getCandidates("20260603", "서울특별시", "3");

        assertThat(response.getCandidates())
                .extracting(ElectionCandidateListResponse.CandidateItem::getCandidateName)
                .containsExactly("확정 후보");
    }

    @Test
    @DisplayName("확정후보가 없으면 예비후보 목록을 반환한다")
    void getCandidatesReturnsPreliminaryCandidatesWhenConfirmedCandidatesMissing() {
        given(candidateRepository.findBySgIdAndSgTypecodeAndSdName("20260603", 3, "서울특별시"))
                .willReturn(List.of(
                        candidate(1L, "예비 후보 A", "PRELIMINARY"),
                        candidate(2L, "예비 후보 B", "PRELIMINARY")
                ));

        ElectionCandidateListResponse response = electionService.getCandidates("20260603", "서울특별시", "3");

        assertThat(response.getCandidates())
                .extracting(ElectionCandidateListResponse.CandidateItem::getCandidateName)
                .containsExactly("예비 후보 A", "예비 후보 B");
    }

    private ElectionCandidate candidate(Long id, String name, String candidateType) {
        return ElectionCandidate.builder()
                .id(id)
                .huboid("huboid-" + id)
                .sgId("20260603")
                .sgTypecode(3)
                .candidateType(candidateType)
                .sdName("서울특별시")
                .sggName("서울특별시")
                .name(name)
                .jdName("테스트정당")
                .build();
    }
}
