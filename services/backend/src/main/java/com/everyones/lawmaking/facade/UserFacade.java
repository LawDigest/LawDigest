package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.response.UserMyPageInfoResponse;
import com.everyones.lawmaking.common.dto.response.WithdrawResponse;
import com.everyones.lawmaking.global.config.OAuthConfig.OAuthServiceFactory;
import com.everyones.lawmaking.global.error.UserException;
import com.everyones.lawmaking.global.error.AuthException;
import com.everyones.lawmaking.global.error.ExternalException;
import com.everyones.lawmaking.global.error.ErrorCode;
import com.everyones.lawmaking.global.service.TokenService;
import com.everyones.lawmaking.global.util.AuthenticationUtil;
import com.everyones.lawmaking.service.AuthService;
import com.everyones.lawmaking.service.OAuthService;
import com.everyones.lawmaking.service.UserService;
import com.everyones.lawmaking.service.LikeService;
import com.everyones.lawmaking.service.NotificationService;
import com.everyones.lawmaking.service.SearchKeywordService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import java.util.Map;
import java.util.Objects;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserFacade {
    private final UserService userService;
    private final AuthService authService;
    private final TokenService tokenService;
    private final OAuthServiceFactory oAuthServiceFactory;
    private final LikeService likeService;
    private final NotificationService notificationService;
    private final SearchKeywordService searchKeywordService;
    private final TransactionTemplate transactionTemplate;

    public UserMyPageInfoResponse getUserMyPageInfo(long userId) {
        return userService.getUserMyPageInfo(userId);
    }

    public WithdrawResponse withdraw(HttpServletRequest httpRequest, HttpServletResponse httpResponse) {
        var userId = AuthenticationUtil.getUserId()
                .orElseThrow(UserException.UserNotFoundException::new);
        var authInfo = authService.getAuthInfo(userId);
        var socialId = authInfo.getSocialId();
        var provider = authInfo.getProvider();
        var oAuthService = oAuthServiceFactory.getOAuthService(provider);
        return transactionTemplate.execute(status -> {
            try {
                tokenService.logout(httpRequest, httpResponse);
                deleteUserAccount(userId, socialId);
                var oAuthResponse = oAuthService.getOAuthTokenResponse(provider, socialId);
                var accessToken = Objects.requireNonNull(oAuthResponse.getBody()).getAccessToken();
                oAuthService.unlink(provider, accessToken);
                return WithdrawResponse.of(authInfo);
            } catch (AuthException | UserException e) {
                status.setRollbackOnly();
                throw e;
            } catch (HttpClientErrorException | HttpServerErrorException e) {
                status.setRollbackOnly();
                String kakaoErrorMessage = e.getResponseBodyAsString();
                throw new ExternalException.ApiException(
                        ErrorCode.EXTERNAL_API_ERROR,
                        Map.of("error Message from social service", kakaoErrorMessage)
                );
            } catch (Exception e) {
                status.setRollbackOnly();
                log.error("Error during user account deletion or unlink", e);
                throw new UserException.WithdrawalFailureException(Map.of("userId", String.valueOf(userId)));
            }
        });
    }

    public void deleteUserAccount(Long userId, String socialId) {
        try{
            likeService.deleteBillLikeByUserId(userId);
            likeService.deleteCongressmanLikeByUserId(userId);
            likeService.deletePartyFollowByUserId(userId);
            notificationService.deleteNotificationByUserId(userId);
            searchKeywordService.deleteAllSearchWordsByUserId(userId);
            int isUserDeleted = userService.deleteUserById(userId);
            if (isUserDeleted == 0) {
                throw new UserException.UserNotFoundException(Map.of("userId", String.valueOf(userId)));
            }
            int isAuthInfoDeleted = authService.deleteAuthInfoBySocialId(socialId);
            if (isAuthInfoDeleted == 0) {
                throw new AuthException.AuthInfoNotFound(Map.of("userId", String.valueOf(userId)));
            }
        } catch (Exception e) {
            log.error("Error during user account deletion", e);
            throw e;
        }
    }

    public void reissueToken(HttpServletRequest httpServletRequest, HttpServletResponse httpServletResponse){
        authService.reissueToken(httpServletRequest, httpServletResponse);
    }
}