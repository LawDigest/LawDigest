package com.everyones.lawmaking.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.when;

import com.everyones.lawmaking.common.dto.BillInfoDto;
import com.everyones.lawmaking.common.dto.bill.BillDto;
import com.everyones.lawmaking.common.dto.response.BillListResponse;
import com.everyones.lawmaking.common.dto.response.PaginationResponse;
import com.everyones.lawmaking.facade.BillFacade;
import com.everyones.lawmaking.facade.LikeFacade;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Pageable;

@ExtendWith(MockitoExtension.class)
class BillControllerTest {
    @Mock
    private BillFacade billFacade;

    @Mock
    private LikeFacade likeFacade;

    @InjectMocks
    private BillController billController;

    @Test
    void mainFeedDoesNotReturnMoreThanRequestedSize() {
        var pageSize = 3;
        when(billFacade.getBillList(org.mockito.ArgumentMatchers.any(Pageable.class), isNull()))
                .thenReturn(BillListResponse.of(
                        PaginationResponse.of(false, 0),
                        List.of(billDto("bill-1"), billDto("bill-2"), billDto("bill-3"), billDto("bill-4"))
                ));

        var response = billController.getBillsFromMainFeed(0, pageSize, null);

        assertThat(response.getData().getBillList())
                .extracting(billDto -> billDto.getBillInfoDto().getBillId())
                .containsExactly("bill-1", "bill-2", "bill-3");

        var pageableCaptor = ArgumentCaptor.forClass(Pageable.class);
        org.mockito.Mockito.verify(billFacade).getBillList(pageableCaptor.capture(), isNull());
        assertThat(pageableCaptor.getValue().getPageSize()).isEqualTo(pageSize);
    }

    private BillDto billDto(String billId) {
        return BillDto.of(
                BillInfoDto.builder()
                        .billId(billId)
                        .title("title " + billId)
                        .build(),
                Collections.emptyList(),
                Collections.emptyList(),
                false
        );
    }
}
