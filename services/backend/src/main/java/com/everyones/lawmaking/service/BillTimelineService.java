package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.projection.CommitteeBillDto;
import com.everyones.lawmaking.repository.BillTimelineRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Slice;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

@Service
@RequiredArgsConstructor
public class BillTimelineService {
    private final BillTimelineRepository billTimelineRepository;



    public List<String> getSubmittedBillIds(LocalDate localDate) {
        return billTimelineRepository.findBillTimelineBetweenProposeDateAndStage(localDate, "접수");
    }

    public List<String> findPromulgationBillIds(LocalDate localDate) {
        return billTimelineRepository.findBillTimelineBetweenProposeDateAndStage(localDate, "공포");
    }

    public List<String> findPlenaryBillIds(LocalDate localDate) {
        return billTimelineRepository.findBillTimelineBetweenProposeDateAndStage(localDate, "본회의 심의");
    }

    public List<CommitteeBillDto> findCommitteesWithMultipleBillIds(LocalDate proposeDate) {
        var tupleList = billTimelineRepository.findCommitteesWithMultipleBills(proposeDate);
        return tupleList.stream()
                .map(tuple -> {
                    String committee = tuple.get("committee", String.class);
                    String billIdsConcat = tuple.get("billIds", String.class);
                    List<String> billIds = Arrays.asList(billIdsConcat.split(","));
                    return CommitteeBillDto.of(committee, billIds);
                }).toList();
    }

    public Slice<LocalDate> getDatePaging(Pageable pageable) {
        return billTimelineRepository.findTopProposeDates(pageable);
    }
    public String getRecentBillResult(String billId) {
        return billTimelineRepository.findTopByBillIdOrderByStatusUpdateDateDesc(billId);
    }
}
