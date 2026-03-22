package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.BillLikeResponse;
import com.everyones.lawmaking.common.dto.response.CongressmanLikeResponse;
import com.everyones.lawmaking.common.dto.response.CountDto;
import com.everyones.lawmaking.common.dto.response.PartyFollowResponse;
import com.everyones.lawmaking.domain.entity.*;
import com.everyones.lawmaking.global.error.LikeException;
import com.everyones.lawmaking.repository.BillLikeRepository;
import com.everyones.lawmaking.repository.CongressmanLikeRepository;
import com.everyones.lawmaking.repository.PartyFollowRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional
public class LikeService {
    private final BillLikeRepository billLikeRepository;
    private final CongressmanLikeRepository congressmanLikeRepository;
    private final PartyFollowRepository partyFollowRepository;


    public Boolean getCongressmanLike(String congressmanId, long userId) {
        var congressmanLike = congressmanLikeRepository.findByUserIdAndCongressmanId(userId, congressmanId);
        return congressmanLike.isPresent();
    }
    public Boolean getFollowParty(long partyId, long userId) {
        var partyFollow = partyFollowRepository.findByUserIdAndPartyId(userId,partyId);
        return partyFollow.isPresent();
    }

    public Boolean getBillLikeChecked(String billId, long userId) {
        var billLike = billLikeRepository.findByUserIdAndBillId(userId, billId);
        return billLike.isPresent();
    }

    public BillLikeResponse likeBill(User user, Bill bill, boolean likeChecked) {
        var billLike = billLikeRepository.findByUserIdAndBillId(user.getId(), bill.getId());
        if (billLike.isPresent()) {
            if (likeChecked) {
                throw new LikeException.UpdateParameterException(Map.of("likeChecked", Boolean.toString(likeChecked)));
            }
            return deleteBillLike(billLike.get());
        }
        if(!likeChecked) {
            throw new LikeException.UpdateParameterException(Map.of("likeChecked", Boolean.toString(likeChecked)));
        }
        return createBillLike(user, bill);
    }


    public CongressmanLikeResponse likeCongressman(User user, Congressman congressman, boolean likeChecked) {
        var congressmanLike = congressmanLikeRepository.findByUserIdAndCongressmanId(user.getId(), congressman.getId());
        if (congressmanLike.isPresent()) {
            if (likeChecked) {
                throw new LikeException.UpdateParameterException(Map.of("likeChecked", Boolean.toString(likeChecked)));
            }
            return deleteCongressmanLike(congressmanLike.get());
        }
        if(!likeChecked) {
            throw new LikeException.UpdateParameterException(Map.of("likeChecked", Boolean.toString(likeChecked)));
        }
        return createCongressmanLike(user, congressman);
    }


    public PartyFollowResponse followParty(User user, Party party, boolean followChecked) {
        var partyFollow = partyFollowRepository.findByUserIdAndPartyId(user.getId(), party.getId());
        if (partyFollow.isPresent()) {
            if (followChecked) {
                throw new LikeException.UpdateParameterException(Map.of("likeChecked", Boolean.toString(followChecked)));
            }
            return deletePartyFollow(partyFollow.get());
        }
        if(!followChecked) {
            throw new LikeException.UpdateParameterException(Map.of("followChecked", Boolean.toString(followChecked)));
        }
        return createPartyFollow(user, party);

    }


    private PartyFollowResponse createPartyFollow(User user, Party party) {
        var partyFollow = PartyFollow.builder()
                .party(party)
                .user(user)
                .build();
        partyFollowRepository.save(partyFollow);
        return PartyFollowResponse.from(true);
    }
    private PartyFollowResponse deletePartyFollow(PartyFollow partyFollow) {
        partyFollowRepository.deleteById(partyFollow.getId());
        return PartyFollowResponse.from(false);
    }


    private CongressmanLikeResponse createCongressmanLike(User user, Congressman congressman) {
        var congressmanLike = com.everyones.lawmaking.domain.entity.CongressmanLike.builder()
                .congressman(congressman)
                .user(user)
                .build();
        congressmanLikeRepository.save(congressmanLike);
        return CongressmanLikeResponse.from(true);
    }

    private CongressmanLikeResponse deleteCongressmanLike(CongressmanLike congressmanLike) {
        congressmanLikeRepository.deleteById(congressmanLike.getId());
        return CongressmanLikeResponse.from(false);
    }

    private BillLikeResponse createBillLike(User user, Bill bill) {
        var billLike = BillLike.builder()
                .bill(bill)
                .user(user)
                .build();
        billLikeRepository.save(billLike);
        return BillLikeResponse.from(true);
    }

    private BillLikeResponse deleteBillLike(BillLike billLike) {
        billLikeRepository.deleteById(billLike.getId());
        return BillLikeResponse.from(false);
    }

    public CountDto getCongressmanLikeCount(long userId) {
        return CountDto.from(congressmanLikeRepository.countByUserId(userId));
    }

    public CountDto getBookmarkedBillCount(long userId) {
        return CountDto.from(billLikeRepository.countByUserId(userId));
    }

    public Integer getCongressmanFollowerCount(String congressmanId) {
        return congressmanLikeRepository.countByCongressmanId(congressmanId).intValue();
    }

    public void deleteCongressmanLikeByUserId(Long userId) {
        congressmanLikeRepository.deleteByUserId(userId);
    }

    public void deleteBillLikeByUserId(Long userId) {
        billLikeRepository.deleteAllByUserId(userId);
    }

    public void deletePartyFollowByUserId(Long userId) {
        partyFollowRepository.deleteAllByUserId(userId);
    }


}
