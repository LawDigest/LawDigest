package com.everyones.lawmaking.global.service;

import com.everyones.lawmaking.domain.entity.Token;
import com.everyones.lawmaking.global.auth.PrincipalDetails;
import com.everyones.lawmaking.global.config.OAuthConfig.AppProperties;
import com.everyones.lawmaking.global.error.AuthException;
import com.everyones.lawmaking.global.error.UserException;
import com.everyones.lawmaking.global.jwt.AuthToken;
import com.everyones.lawmaking.global.jwt.AuthTokenProvider;
import com.everyones.lawmaking.global.util.AuthenticationUtil;
import com.everyones.lawmaking.global.util.CookieUtil;
import com.everyones.lawmaking.repository.TokenRepository;
import com.everyones.lawmaking.repository.UserRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.HashMap;
import java.util.Map;

import static com.everyones.lawmaking.repository.OAuth2AuthorizationRequestBasedOnCookieRepository.*;

@Service
@RequiredArgsConstructor
public class TokenService {

    private final UserRepository userRepository;

    private final TokenRepository tokenRepository;

    private final AuthTokenProvider tokenProvider;

    private final AppProperties appProperties;


    private static final String PROVIDER = "provider";


    public Map<String, String> issueToken(Authentication authentication) {


        PrincipalDetails principalDetails = (PrincipalDetails) authentication.getPrincipal();
        var userLocalId = principalDetails.getUserId();
        var userSocialId = principalDetails.getSocialId();
        var userRole = principalDetails.getRole();
        var userProvider = principalDetails.getProviderType();


        Map<String, String> authTokenMap = new HashMap<>();
        // access 토큰 설정
        var now = new Date();

        long minutes = 1000 * 60;

        AuthToken accessToken = tokenProvider.createAuthToken(
                userLocalId,
                userRole.getCode(),
                new Date(now.getTime() + appProperties.getAccessTokenExpiry() * minutes)
        );

        // refresh 토큰 설정

        AuthToken refreshToken = tokenProvider.createAuthToken(
                new Date(now.getTime() + appProperties.getRefreshTokenExpiry() * minutes)
        );

        var accessTokenForUse = accessToken.getToken();
        var refreshTokenForUse = refreshToken.getToken();

        var savedUser = userRepository.findUserBySocialIdAndProvider(userSocialId, userProvider)
                .orElseThrow(() -> new UserException.UserNotFoundException(Map.of("userProvider", userProvider.toString())));

        var tokenData = Token.builder()
                .user(savedUser)
                .role(savedUser.getRole())
                .refreshToken(refreshTokenForUse)
                .build();

        tokenRepository.save(tokenData);

        authTokenMap.put("accessToken", accessTokenForUse);
        authTokenMap.put("refreshToken", refreshTokenForUse);

        return authTokenMap;
    }

    public Map<String, String> reissueToken(String refreshTokenFromCookie) throws AuthException {

        // 쿠키에서 가져온 refresh token으로 token 행 가져오기
        var savedToken = tokenRepository.findTokenByRefreshToken(refreshTokenFromCookie)
                .orElseThrow(AuthException.TokenNotFound::new);

        var refreshTokenForUse = savedToken.getRefreshToken();

        // 가져온 refreshToken 검증
        var refreshTokenForAuthToken = tokenProvider.convertAuthToken(refreshTokenForUse);

        //refreshToken 검사
        if (!refreshTokenForAuthToken.validate() || !refreshTokenForUse.equals(refreshTokenFromCookie)) {
            throw new AuthException.TokenNotValid();
        }


        Map<String, String> authTokenMap = new HashMap<>();
        // access 토큰 설정
        var now = new Date();
        var role = savedToken.getRole();

        long minutes = 1000 * 60;

        AuthToken newAccessToken = tokenProvider.createAuthToken(
                savedToken.getUser().getId(),
                role.getCode(),
                new Date(now.getTime() + appProperties.getAccessTokenExpiry() * minutes)
        );

        // refresh 토큰 설정

        AuthToken newRefreshToken = tokenProvider.createAuthToken(
                new Date(now.getTime() + appProperties.getRefreshTokenExpiry() * minutes)
        );

        var newAccessTokenForUse = newAccessToken.getToken();
        var newRefreshTokenForUse = newRefreshToken.getToken();


        var tokenData = Token.builder()
                .user(savedToken.getUser())
                .role(savedToken.getUser().getRole())
                .refreshToken(newRefreshToken.getToken())
                .build();

        tokenRepository.findTokenByRefreshToken(refreshTokenForUse)
                .ifPresent(tokenRepository::delete);

        tokenRepository.save(tokenData);

        authTokenMap.put("accessToken", newAccessTokenForUse);
        authTokenMap.put("refreshToken", newRefreshTokenForUse);


        return authTokenMap;
    }

    @Transactional
    public void invalidateToken(Long userId) {
        deleteByUserId(userId);
    }



    @Transactional
    public void logout(HttpServletRequest httpServletRequest, HttpServletResponse httpServletResponse) {

        var userId = AuthenticationUtil.getUserId();
        if(userId.isPresent()){
            invalidateToken(userId.get());
        }
        HttpSession session = httpServletRequest.getSession(false); // 기존 세션 가져오기
        if (session != null) {
            session.invalidate();
        }
        var cookieDomain = appProperties.getCookieDomain();
        CookieUtil.deleteCookieForClient(httpServletRequest, httpServletResponse, ACCESS_TOKEN, cookieDomain);
        CookieUtil.deleteCookie(httpServletRequest, httpServletResponse, REFRESH_TOKEN);
        CookieUtil.deleteCookie(httpServletRequest, httpServletResponse, JSESSIONID);

        SecurityContext context = SecurityContextHolder.getContext();
        context.setAuthentication(null);
        SecurityContextHolder.clearContext();

    }

    @Transactional
    public void deleteByUserId(Long userId) {
        tokenRepository.deleteByUserId(userId);
    }


}
