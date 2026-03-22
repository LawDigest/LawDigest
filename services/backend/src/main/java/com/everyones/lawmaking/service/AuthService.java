package com.everyones.lawmaking.service;

import com.everyones.lawmaking.domain.entity.AuthInfo;
import com.everyones.lawmaking.global.config.OAuthConfig.AppProperties;
import com.everyones.lawmaking.global.error.AuthException;
import com.everyones.lawmaking.global.service.TokenService;
import com.everyones.lawmaking.global.util.CookieUtil;
import com.everyones.lawmaking.repository.AuthInfoRepository;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;

import static com.everyones.lawmaking.repository.OAuth2AuthorizationRequestBasedOnCookieRepository.*;


@RequiredArgsConstructor
@Service
@Slf4j
@Transactional(readOnly = true)
public class AuthService {

    private final AuthInfoRepository authInfoRepository;
    private final AppProperties appProperties;
    private final TokenService tokenService;
    private static final String TARGET_ID_TYPE = "user_id";


    @Transactional
    public void reissueToken(HttpServletRequest httpServletRequest, HttpServletResponse httpServletResponse) {
        // 쿠키에서 Refresh Token 가져오기

        String refreshTokenCookie = getCookieValue(httpServletRequest,REFRESH_TOKEN);


        if (refreshTokenCookie == null) {
            //로그아웃
            tokenService.logout(httpServletRequest,httpServletResponse);
            return;
        }

        //토큰 재발급
        Map<String, String> tokenMap;

        try {
            tokenMap = tokenService.reissueToken(refreshTokenCookie);
        } catch (AuthException e) {
            // 예외 발생 시 로그아웃 메서드 호출
            tokenService.logout(httpServletRequest, httpServletResponse);
            return;
        } catch (Exception e){
            log.error("Unexpected exception was caused",e);
            // 예외 발생 시 로그아웃 메서드 호출
            tokenService.logout(httpServletRequest, httpServletResponse);
            return;
        }
        var cookieDomain = appProperties.getCookieDomain();

        // 쿠키 설정
        setCookies(httpServletRequest, httpServletResponse, tokenMap, appProperties, cookieDomain);
    }

    private void setCookies(HttpServletRequest httpServletRequest,HttpServletResponse httpServletResponse, Map<String, String> tokenMap, AppProperties appProperties, String cookieDomain) {
        int minutes = 1000 * 60;
        int refreshTokenExpiry = (int) appProperties.getRefreshTokenExpiry() * minutes;
        int accessTokenExpiry = (int) appProperties.getAccessTokenExpiry() * minutes;

        CookieUtil.deleteCookieForClient(httpServletRequest, httpServletResponse, ACCESS_TOKEN, cookieDomain);
        CookieUtil.deleteCookie(httpServletRequest, httpServletResponse, REFRESH_TOKEN);
        CookieUtil.deleteCookie(httpServletRequest, httpServletResponse, JSESSIONID);

        CookieUtil.addCookie(httpServletResponse, REFRESH_TOKEN, tokenMap.get("refreshToken"), refreshTokenExpiry);
        CookieUtil.addCookieForClient(httpServletResponse, ACCESS_TOKEN, tokenMap.get("accessToken"), accessTokenExpiry, cookieDomain);
    }
    private String getCookieValue(HttpServletRequest httpServletRequest, String name) {
        Cookie[] cookies = httpServletRequest.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if (name.equals(cookie.getName())) {
                    return cookie.getValue();
                }
            }
        }
        return null;
    }
    public AuthInfo getAuthInfo(Long userId) {
        return authInfoRepository.findAuthInfoByUserId(userId)
                .orElseThrow(() -> new AuthException.AuthInfoNotFound(Map.of("userId", String.valueOf(userId))));
    }

    public  int deleteAuthInfoBySocialId(String socialId) {
        return authInfoRepository.deleteBySocialId(socialId);
    }

}
