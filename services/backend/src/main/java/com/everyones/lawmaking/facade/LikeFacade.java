package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.response.BillLikeResponse;
import com.everyones.lawmaking.common.dto.response.CongressmanLikeResponse;
import com.everyones.lawmaking.common.dto.response.PartyFollowResponse;
import com.everyones.lawmaking.service.LikeService;
import com.everyones.lawmaking.service.UserService;
import com.everyones.lawmaking.service.BillService;
import com.everyones.lawmaking.service.CongressmanService;
import com.everyones.lawmaking.service.PartyService;
import com.everyones.lawmaking.service.RedisService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class LikeFacade {
    private final LikeService likeService;
    private final UserService userService;
    private final BillService billService;
    private final CongressmanService congressmanService;
    private final PartyService partyService;
    private final RedisService redisService;

    @Transactional
    public BillLikeResponse likeBill(long userId, String billId, boolean likeChecked) {
        var user = userService.findById(userId);
        var bill = billService.findById(billId);
        if (likeChecked) {
            redisService.addToLikesQueue(billId);
        }
        return likeService.likeBill(user, bill, likeChecked);
    }

    @Transactional
    public CongressmanLikeResponse likeCongressman(long userId, String congressmanId, boolean likeChecked) {
        var user = userService.findById(userId);
        var congressman = congressmanService.findById(congressmanId);
        return likeService.likeCongressman(user, congressman, likeChecked);
    }

    @Transactional
    public PartyFollowResponse followParty(long userId, long partyId, boolean followChecked) {
        var user = userService.findById(userId);
        var party = partyService.findById(partyId);
        return likeService.followParty(user, party, followChecked);
    }
} 