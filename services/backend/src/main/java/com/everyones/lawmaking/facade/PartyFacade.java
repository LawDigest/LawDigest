package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.response.PartyDetailResponse;
import com.everyones.lawmaking.common.dto.response.PartyCongressmanResponse;
import com.everyones.lawmaking.common.dto.response.FollowingPartyResponse;
import com.everyones.lawmaking.common.dto.response.ParliamentaryPartyResponse;
import com.everyones.lawmaking.common.dto.response.PartyExecutiveResponse;
import com.everyones.lawmaking.service.PartyService;
import com.everyones.lawmaking.service.CongressmanService;
import com.everyones.lawmaking.service.LikeService;
import com.everyones.lawmaking.global.util.AuthenticationUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class PartyFacade {
    private final PartyService partyService;
    private final CongressmanService congressmanService;
    private final LikeService likeService;

    public PartyDetailResponse getPartyById(long partyId) {
        var partyDetailResponse =  partyService.getPartyById(partyId);
        var totalCongressmanCount = congressmanService.getTotalCongressmanState(true);
        partyDetailResponse.setTotalCongressmanCount(totalCongressmanCount);
        var userId = AuthenticationUtil.getUserId();
        if (userId.isEmpty()) {
            return partyDetailResponse;
        }
        var followChecked = likeService.getFollowParty(partyId, userId.get());
        partyDetailResponse.setFollowed(followChecked);
        return partyDetailResponse;
    }

    public PartyCongressmanResponse getPartyCongressman(long partyId) {
        return congressmanService.getPartyCongressman(partyId);
    }

    public List<FollowingPartyResponse> getFollowingParty(long userId) {
        return partyService.getFollowingParty(userId);
    }

    public List<ParliamentaryPartyResponse> getParliamentaryParty() {
        return partyService.getParliamentaryParty();
    }

    public PartyExecutiveResponse getPartyExecutive(int partyId) {
        var party = partyService.findById(partyId);
        return PartyExecutiveResponse.from(party);
    }
} 