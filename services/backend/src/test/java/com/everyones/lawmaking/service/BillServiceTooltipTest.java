package com.everyones.lawmaking.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import com.everyones.lawmaking.domain.entity.Bill;
import com.everyones.lawmaking.repository.BillReportTooltipQueryRepository;
import com.everyones.lawmaking.repository.BillRepository;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class BillServiceTooltipTest {
    @Mock
    private BillRepository billRepository;

    @Mock
    private BillReportTooltipQueryRepository billReportTooltipQueryRepository;

    @InjectMocks
    private BillService billService;

    @Test
    void billListUsesOnlyCurrentAppliedTooltipSummaries() {
        var first = bill("bill-1", "원본 리포트 1");
        var second = bill("bill-2", "원본 리포트 2");
        when(billRepository.findBillInfoByIdList(List.of("bill-1", "bill-2")))
                .thenReturn(List.of(first, second));
        when(billReportTooltipQueryRepository.findCurrentRenderedSummaries(List.of("bill-1", "bill-2")))
                .thenReturn(Map.of("bill-1", "{{법률용어:설명}}가 포함된 리포트"));

        var result = billService.getBillListResponse(List.of("bill-1", "bill-2"));

        assertThat(result)
                .extracting(item -> item.getBillInfoDto().getGptSummary())
                .containsExactly("{{법률용어:설명}}가 포함된 리포트", "원본 리포트 2");
    }

    private Bill bill(String billId, String gptSummary) {
        return Bill.builder()
                .id(billId)
                .billName("테스트 법안 " + billId)
                .gptSummary(gptSummary)
                .billLike(new ArrayList<>())
                .representativeProposer(new ArrayList<>())
                .publicProposer(new ArrayList<>())
                .build();
    }
}
