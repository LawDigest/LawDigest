package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.OAuthTokenResponse;
import com.everyones.lawmaking.domain.entity.Provider;
import com.everyones.lawmaking.global.error.SocialTokenException;
import com.everyones.lawmaking.repository.OAuth2ClientTokenRepository;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@RequiredArgsConstructor
@Service
@Slf4j
@Transactional(readOnly = true)
public abstract class OAuthService {
    private final OAuth2ClientTokenRepository oAuth2ClientTokenRepository;
    private static final String PRINCIPAL_NAME_STRING = "socialTokenPrincipalName";

    public abstract Provider getProvider();

    protected String getRecentSavedRefreshToken(Provider provider, String socialId) {
            return oAuth2ClientTokenRepository.findTop1ByClientRegistrationIdAndPrincipalNameOrderByCreatedDateDesc(provider.name(), socialId)
                .orElseThrow(() -> new SocialTokenException.SocialTokenNotFound(Map.of(PRINCIPAL_NAME_STRING, socialId)))
                .getRefreshToken();
    }
    //소셜 엑세스토큰 재발급 로직
    // 데이터베이스에 저장된 소셜 리프레시토큰을 활용해 엑세스토큰 발급
    public abstract ResponseEntity<OAuthTokenResponse> getOAuthTokenResponse(Provider provider, String socialId);

    //소셜 연결 끊기
    public abstract void unlink(Provider provider, String accessToken);

}
