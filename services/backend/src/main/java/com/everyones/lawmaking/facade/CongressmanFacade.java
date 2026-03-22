package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.response.CongressmanResponse;
import com.everyones.lawmaking.common.dto.response.LikingCongressmanResponse;
import com.everyones.lawmaking.service.CongressmanService;
import com.everyones.lawmaking.service.LikeService;
import com.everyones.lawmaking.service.RepresentativeProposerService;
import com.everyones.lawmaking.service.BillProposerService;
import com.everyones.lawmaking.global.util.AuthenticationUtil;
import com.everyones.lawmaking.common.dto.response.CountDto;
import com.everyones.lawmaking.global.error.AuthException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class CongressmanFacade {
    private final CongressmanService congressmanService;
    private final LikeService likeService;
    private final RepresentativeProposerService representativeProposerService;
    private final BillProposerService billProposerService;

    public CongressmanResponse getCongressman(String congressmanId) {
        var congressman = congressmanService.getCongressman(congressmanId);
        var followCount = likeService.getCongressmanFollowerCount(congressmanId);
        var representCount = representativeProposerService.countBillByCongressmanAsPublicProposer(congressmanId);
        var publicCount = billProposerService.countBillByCongressmanAsPublicProposer(congressmanId);
        var userId = AuthenticationUtil.getUserId();
        if (userId.isEmpty()) {
            return CongressmanResponse.of(congressman, followCount, representCount, publicCount);
        }
        var congressmanLike = likeService.getCongressmanLike(congressmanId, userId.get());
        return CongressmanResponse.of(congressman, followCount, representCount, publicCount, congressmanLike);
    }

    public CountDto getCongressmanLikeCount() {
        var userId = AuthenticationUtil.getUserId();
        if (userId.isEmpty()) {
            throw new AuthException.AuthInfoNotFound();
        }
        return likeService.getCongressmanLikeCount(userId.get());
    }

    public List<LikingCongressmanResponse> getLikingCongressman(long userId) {
        return congressmanService.getLikingCongressman(userId);
    }
} 