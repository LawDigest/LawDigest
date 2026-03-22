package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.PartyVoteDto;
import com.everyones.lawmaking.common.dto.VoteResultResponse;
import com.everyones.lawmaking.common.dto.bill.BillDto;
import com.everyones.lawmaking.common.dto.response.BillDetailResponse;
import com.everyones.lawmaking.common.dto.response.BillListResponse;
import com.everyones.lawmaking.common.dto.response.BillStateCountResponse;
import com.everyones.lawmaking.common.dto.response.BillViewCountResponse;
import com.everyones.lawmaking.common.dto.response.CountDto;
import com.everyones.lawmaking.global.util.AuthenticationUtil;
import com.everyones.lawmaking.service.BillService;
import com.everyones.lawmaking.service.LikeService;
import com.everyones.lawmaking.service.RedisService;
import com.everyones.lawmaking.service.VotePartyService;
import com.everyones.lawmaking.service.VoteRecordService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class BillFacade {
    private final BillService billService;
    private final LikeService likeService;
    private final VoteRecordService voteRecordService;
    private final VotePartyService votePartyService;
    private final RedisService redisService;

    public BillDetailResponse getBillByBillId(String billId) {
        var billDto =  billService.getBillWithDetail(billId);
        var userId = AuthenticationUtil.getUserId();
        var voteRecord = voteRecordService.getVoteRecordByBillId(billId);
        var votePartyList = votePartyService.getVotePartyListWithPartyByBillId(billId).stream()
                .map(PartyVoteDto::from)
                .toList();
        var voteResultResponse = VoteResultResponse.of(voteRecord, votePartyList);
        billDto.setVoteResultResponse(voteResultResponse);
        if (userId.isEmpty()) {
            return billDto;
        }
        var isBookMark = likeService.getBillLikeChecked(billDto.getBillInfoDto().getBillId(), userId.get());
        billDto.setIsBookMark(isBookMark);
        return billDto;
    }

    public BillViewCountResponse updateViewCount(String billId) {
        redisService.addToViewsQueue(billId);
        return billService.updateViewCount(billId);
    }

    public BillListResponse getBillsFromRepresentativeProposer(String congressmanId, Pageable pageable, String stage) {
        var billListResponse = stage == null ? billService.getBillInfoFromRepresentativeProposer(congressmanId, pageable)
                : billService.getBillInfoFromRepresentativeProposer(congressmanId, pageable, stage);
        return setBillListResponseBookMark(billListResponse);
    }

    public BillListResponse getBillsFromPublicProposer(String congressmanId, Pageable pageable, String stage) {
        var billListResponse = stage == null ? billService.getBillInfoFromPublicProposer(congressmanId, pageable)
                : billService.getBillInfoFromPublicProposer(congressmanId, pageable, stage);
        return setBillListResponseBookMark(billListResponse);
    }

    public BillListResponse getRepresentativeBillsByParty(Pageable pageable, long partyId, String stage) {
        var billListResponse = stage == null ? billService.getRepresentativeBillsByParty(pageable, partyId)
                : billService.getRepresentativeBillsByParty(pageable, partyId, stage);
        return setBillListResponseBookMark(billListResponse);
    }

    public BillListResponse getPublicBillsByParty(Pageable pageable, long partyId, String stage) {
        var billListResponse = stage == null ? billService.getPublicBillsByParty(pageable, partyId)
                : billService.getPublicBillsByParty(pageable, partyId, stage);
        return setBillListResponseBookMark(billListResponse);
    }

    public BillListResponse getBookmarkedBills(Pageable pageable, long userId) {
        var billListResponse = billService.getBookmarkingBills(pageable, userId);
        return setBillListResponseBookMark(billListResponse);
    }

    public List<BillDto> getPopularBills() {
        var popularBillIds = redisService.getPopularBills();
        var billList = billService.getBillListResponse(popularBillIds);
        var userIdOptional = AuthenticationUtil.getUserId();
        return userIdOptional.map(userId -> billList.stream()
                .map(billDto -> {
                    var isBookMark = likeService.getBillLikeChecked(billDto.getBillInfoDto().getBillId(), userId);
                    billDto.setIsBookMark(isBookMark);
                    return billDto;
                })
                .toList()).orElse(billList);
    }

    public BillListResponse getBillsFromFollowingTab(Pageable pageable) {
        var billList =  billService.findByUserAndCongressmanLike(pageable);
        return setBillListResponseBookMark(billList);
    }

    private BillListResponse setBillListResponseBookMark(BillListResponse billListResponse) {
        var userId = AuthenticationUtil.getUserId();
        if (userId.isEmpty()) {
            return billListResponse;
        }
        var billList = billListResponse.getBillList().stream()
                .map(billDto -> {
                    var isBookMark = likeService.getBillLikeChecked(billDto.getBillInfoDto().getBillId(), userId.get());
                    billDto.setIsBookMark(isBookMark);
                    return billDto;
                })
                .toList();
        billListResponse.setBillList(billList);
        return billListResponse;
    }
    @Transactional(readOnly = true)
    public BillStateCountResponse getBillStateCount() {
        return billService.getBillStateCount();
    }
    @Transactional(readOnly = true)
    public BillListResponse getBillList(Pageable pageable, String stage) {
        return billService.getBillList(pageable, stage);
    }
    public CountDto getBookmarkedBillCount() {
        var userId = AuthenticationUtil.getUserId();
        return likeService.getBookmarkedBillCount(userId.get());
    }
}
