package com.everyones.lawmaking.service.election.feed;

import com.everyones.lawmaking.common.dto.response.election.ElectionFeedItem;
import com.everyones.lawmaking.common.dto.response.election.feed.BillFeedPayload;
import com.everyones.lawmaking.domain.entity.Bill;
import com.everyones.lawmaking.repository.BillRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;

@Component
@RequiredArgsConstructor
public class ElectionFeedBillProvider implements ElectionFeedProvider {

    private static final int ASSEMBLY_NUMBER = 22;

    private final BillRepository billRepository;

    @Override
    public String getType() {
        return "bill";
    }

    @Override
    public List<ElectionFeedItem> fetch(String electionId, String cursorDate, String cursorId,
                                         int limit, String party, String regionCode) {
        List<Bill> bills;
        PageRequest page = PageRequest.of(0, limit);

        if (cursorDate == null || cursorId == null) {
            bills = billRepository.findFeedItemsFirst(ASSEMBLY_NUMBER, page);
        } else {
            LocalDate parsedDate = LocalDate.parse(cursorDate.substring(0, 10), DateTimeFormatter.ISO_LOCAL_DATE);
            bills = billRepository.findFeedItems(ASSEMBLY_NUMBER, parsedDate, cursorId, page);
        }

        return bills.stream()
                .map(bill -> ElectionFeedItem.of(
                        "bill-" + bill.getId(),
                        getType(),
                        bill.getProposeDate() != null
                                ? bill.getProposeDate().atStartOfDay().format(DateTimeFormatter.ISO_DATE_TIME)
                                : null,
                        BillFeedPayload.from(bill)
                ))
                .toList();
    }
}
