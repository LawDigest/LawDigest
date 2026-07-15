package com.everyones.lawmaking.common.dto;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

class BillTitleJsonContractTest {
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    void billInfoUsesTitleKey() {
        var dto = BillInfoDto.builder()
                .billId("bill-1")
                .title("카드 제목")
                .build();

        var json = objectMapper.valueToTree(dto);

        assertThat(json.get("title").asText()).isEqualTo("카드 제목");
        assertThat(json.has("brief_summary")).isFalse();
    }

    @Test
    void billOutlineUsesSnakeCaseBillTitleKey() {
        var dto = BillOutlineDto.builder()
                .billId("bill-1")
                .billTitle("카드 제목")
                .build();

        var json = objectMapper.valueToTree(dto);

        assertThat(json.get("bill_title").asText()).isEqualTo("카드 제목");
        assertThat(json.has("bill_brief_summary")).isFalse();
    }

    @Test
    void similarBillUsesCamelCaseBillTitleKey() {
        var dto = SimilarBill.builder()
                .billId("bill-1")
                .billTitle("카드 제목")
                .build();

        var json = objectMapper.valueToTree(dto);

        assertThat(json.get("billTitle").asText()).isEqualTo("카드 제목");
        assertThat(json.has("billBriefSummary")).isFalse();
    }
}
