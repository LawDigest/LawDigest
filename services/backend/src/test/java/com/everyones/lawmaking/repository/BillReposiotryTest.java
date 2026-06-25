package com.everyones.lawmaking.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.everyones.lawmaking.domain.entity.Bill;
import com.everyones.lawmaking.domain.entity.IngestStatusType;
import com.everyones.lawmaking.global.config.QuerydslConfig;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.context.annotation.Import;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.ActiveProfiles;

@DataJpaTest
@ActiveProfiles("test")
public class BillReposiotryTest {
    @SpringBootConfiguration
    @EnableAutoConfiguration
    @EntityScan(basePackageClasses = Bill.class)
    @EnableJpaRepositories(basePackageClasses = BillRepository.class)
    @Import(QuerydslConfig.class)
    static class TestJpaConfig {
    }

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private BillRepository billRepository;

    @Test
    void mainFeedOnlyReturnsBillsWithBriefAndGptSummary() {
        persistReadyBill("summarized", "짧은 요약", "상세 요약");
        persistReadyBill("missing-brief", null, "상세 요약");
        persistReadyBill("missing-gpt", "짧은 요약", null);
        persistReadyBill("blank-brief", " ", "상세 요약");
        persistReadyBill("blank-gpt", "짧은 요약", " ");
        entityManager.flush();

        var response = billRepository.findBillWithDetailAndPage(PageRequest.of(0, 10), Optional.empty(), null);

        assertThat(response.getBillList())
                .extracting(billDto -> billDto.getBillInfoDto().getBillId())
                .containsExactly("summarized");
    }

    @Test
    void feedBillInfoByIdListOnlyReturnsBillsWithBriefAndGptSummary() {
        persistReadyBill("summarized", "짧은 요약", "상세 요약");
        persistReadyBill("missing-brief", null, "상세 요약");
        persistReadyBill("missing-gpt", "짧은 요약", null);
        entityManager.flush();

        var bills = billRepository.findFeedBillInfoByIdList(List.of("summarized", "missing-brief", "missing-gpt"));

        assertThat(bills)
                .extracting(Bill::getId)
                .containsExactly("summarized");
    }

    private void persistReadyBill(String billId, String briefSummary, String gptSummary) {
        entityManager.persist(Bill.builder()
                .id(billId)
                .billNumber(Math.abs(billId.hashCode()))
                .assemblyNumber(22)
                .billName("테스트 법안 " + billId)
                .proposeDate(LocalDate.of(2026, 6, 1))
                .stage("접수")
                .summary("원문 요약")
                .briefSummary(briefSummary)
                .gptSummary(gptSummary)
                .ingestStatus(IngestStatusType.READY)
                .billLike(new ArrayList<>())
                .build());
    }

}
