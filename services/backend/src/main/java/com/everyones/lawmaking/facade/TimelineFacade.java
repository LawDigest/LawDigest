package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.BillOutlineDto;
import com.everyones.lawmaking.common.dto.CommitteeAuditDto;
import com.everyones.lawmaking.common.dto.PartyVoteDto;
import com.everyones.lawmaking.common.dto.PlenaryDto;
import com.everyones.lawmaking.common.dto.response.BillTimelinePaginationResponse;
import com.everyones.lawmaking.common.dto.response.BillTimelineResponse;
import com.everyones.lawmaking.service.BillService;
import com.everyones.lawmaking.service.BillTimelineService;
import com.everyones.lawmaking.service.RedisService;
import com.everyones.lawmaking.service.VotePartyService;
import com.everyones.lawmaking.service.VoteRecordService;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class TimelineFacade {
    private final BillTimelineService billTimelineService;
    private final BillService billService;
    private final VotePartyService votePartyService;
    private final VoteRecordService voteRecordService;
    private final RedisService redisService;

    @Transactional(readOnly = true)
    public BillTimelinePaginationResponse getTimeline(Pageable pageable) {
        var timelineDateList = billTimelineService.getDatePaging(pageable);
        var paginationResponse = com.everyones.lawmaking.common.dto.response.PaginationResponse.from(timelineDateList);
        List<BillTimelineResponse> timelineList = new ArrayList<>();
        for (LocalDate timelineDate : timelineDateList) {
            timelineList.add(getTimeline(timelineDate));
        }
        return BillTimelinePaginationResponse.of(paginationResponse, timelineList);
    }

    @Transactional(readOnly = true)
    public BillTimelineResponse getTimeline(LocalDate proposeDate) {
        if (redisService.isTimelineCached(proposeDate)) {
            return redisService.getTimelineCached(proposeDate);
        }
        var submittedBills = getSubmittedBills(proposeDate);
        var plenaryBills  = getPlenaryBills(proposeDate);
        var promulgationBills = getPromulgationBills(proposeDate);
        var committeeBills = getCommitteeBills(proposeDate);
        return BillTimelineResponse.of(proposeDate, submittedBills,plenaryBills, promulgationBills, committeeBills);
    }

    public List<BillOutlineDto> getSubmittedBills(LocalDate proposeDate) {
        var submittedBillIds = billTimelineService.getSubmittedBillIds(proposeDate);
        var bills = billService.findBillsWithPartiesByIds(submittedBillIds);
        return bills.stream()
                .map(BillOutlineDto::from)
                .toList();
    }
    public List<BillOutlineDto> getPromulgationBills(LocalDate localDate) {
        var promulgationBillIds = billTimelineService.findPromulgationBillIds(localDate);
        var bills = billService.findBillsWithPartiesByIds(promulgationBillIds);
        return bills.stream()
                .map(BillOutlineDto::from)
                .toList();
    }
    public List<PlenaryDto> getPlenaryBills(LocalDate localDate) {
        var plenaryBillIds = billTimelineService.findPlenaryBillIds(localDate);
        var plenaryBills = new ArrayList<PlenaryDto>();
        billService.findBillsWithPartiesByIds(plenaryBillIds)
                .forEach(bill -> {
                    var voteRecord = voteRecordService.getVoteRecordByBillId(bill.getId());
                    var votePartyList = votePartyService.getVotePartyListWithPartyByBillId(bill.getId()).stream()
                            .map(PartyVoteDto::from)
                            .toList();
                    var plenaryBill = PlenaryDto.of(bill, voteRecord, votePartyList);
                    plenaryBills.add(plenaryBill);
                });
        return plenaryBills;
    }
    public List<CommitteeAuditDto> getCommitteeBills(LocalDate proposeDate) {
        var committeeBillDtoList = billTimelineService.findCommitteesWithMultipleBillIds(proposeDate);
        return committeeBillDtoList.stream()
                .map(committeeBillDto -> {
                    var bills = billService.findBillsWithPartiesByIds(committeeBillDto.getBillIds());
                    var billOutlineDtoList = bills.stream()
                            .map(BillOutlineDto::from)
                            .toList();
                    return CommitteeAuditDto.of(committeeBillDto.getCommitteeName(), billOutlineDtoList);
                })
                .toList();
    }
} 