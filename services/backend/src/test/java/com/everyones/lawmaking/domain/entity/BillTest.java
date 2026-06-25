package com.everyones.lawmaking.domain.entity;

import static org.assertj.core.api.Assertions.assertThat;

import com.everyones.lawmaking.common.dto.request.BillDfRequest;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.Test;

class BillTest {
    @Test
    void createsReadyBillOnlyWhenBriefAndGptSummaryExist() {
        var bill = Bill.of(billRequest("bill-1", "짧은 요약", "상세 요약"));

        assertThat(bill.getIngestStatus()).isEqualTo(IngestStatusType.READY);
    }

    @Test
    void createsPartialBillWhenBriefSummaryIsMissing() {
        var bill = Bill.of(billRequest("bill-1", null, "상세 요약"));

        assertThat(bill.getIngestStatus()).isEqualTo(IngestStatusType.PARTIAL);
    }

    @Test
    void createsPartialBillWhenGptSummaryIsMissing() {
        var bill = Bill.of(billRequest("bill-1", "짧은 요약", null));

        assertThat(bill.getIngestStatus()).isEqualTo(IngestStatusType.PARTIAL);
    }

    @Test
    void updatesReadyBillToPartialWhenSummaryFieldsAreMissing() {
        var bill = Bill.of(billRequest("bill-1", "짧은 요약", "상세 요약"));

        bill.updateContent(billRequest("bill-1", "짧은 요약", " "));

        assertThat(bill.getIngestStatus()).isEqualTo(IngestStatusType.PARTIAL);
    }

    private BillDfRequest billRequest(String billId, String briefSummary, String gptSummary) {
        return new BillDfRequest(
                billId,
                Math.abs(billId.hashCode()),
                "테스트 법안",
                "접수",
                null,
                22,
                "원문 요약",
                gptSummary,
                briefSummary,
                LocalDate.of(2026, 6, 1),
                "테스트 발의자",
                List.of(),
                List.of(),
                "의원"
        );
    }
}
