package com.everyones.lawmaking.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.everyones.lawmaking.common.dto.request.BillDfRequest;
import com.everyones.lawmaking.domain.entity.Bill;
import com.everyones.lawmaking.repository.BillProposerRepository;
import com.everyones.lawmaking.repository.BillRepository;
import com.everyones.lawmaking.repository.BillTimelineRepository;
import com.everyones.lawmaking.repository.CongressmanRepository;
import com.everyones.lawmaking.repository.CongressmanRepositoryCustom;
import com.everyones.lawmaking.repository.PartyRepository;
import com.everyones.lawmaking.repository.PartyRepositoryCustom;
import com.everyones.lawmaking.repository.RepresentativeProposerRepository;
import com.everyones.lawmaking.repository.VotePartyRepository;
import com.everyones.lawmaking.repository.VoteRecordRepository;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class DataServiceTest {
    @Mock
    private BillRepository billRepository;
    @Mock
    private CongressmanRepository congressmanRepository;
    @Mock
    private BillProposerRepository billProposerRepository;
    @Mock
    private RepresentativeProposerRepository representativeProposerRepository;
    @Mock
    private PartyRepository partyRepository;
    @Mock
    private BillTimelineRepository billTimelineRepository;
    @Mock
    private VoteRecordRepository voteRecordRepository;
    @Mock
    private VotePartyRepository votePartyRepository;
    @Mock
    private CongressmanRepositoryCustom congressmanRepositoryCustom;
    @Mock
    private PartyRepositoryCustom partyRepositoryCustom;

    @InjectMocks
    private DataService dataService;

    @Test
    void doesNotInsertNewBillWhenSummaryIsMissing() {
        dataService.insertBillInfoDf(List.of(billRequest("bill-without-summary", null)));

        verify(billRepository, never()).save(any(Bill.class));
    }

    @Test
    void doesNotInsertNewBillWhenSummaryIsBlank() {
        dataService.insertBillInfoDf(List.of(billRequest("bill-without-summary", " ")));

        verify(billRepository, never()).save(any(Bill.class));
    }

    @Test
    void doesNotOverwriteExistingBillWhenSummaryIsMissing() {
        var bill = Bill.of(billRequest("existing-bill", "기존 원문 요약"));

        dataService.insertBillInfoDf(List.of(billRequest("existing-bill", null)));

        assertThat(bill.getSummary()).isEqualTo("기존 원문 요약");
        verify(billRepository, never()).save(any(Bill.class));
    }

    private BillDfRequest billRequest(String billId, String summary) {
        return new BillDfRequest(
                billId,
                Math.abs(billId.hashCode()),
                "테스트 법안",
                "접수",
                null,
                22,
                summary,
                "상세 요약",
                "짧은 요약",
                LocalDate.of(2026, 6, 1),
                "테스트 발의자",
                List.of(),
                List.of(),
                "의원"
        );
    }
}
