package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.OAuthTokenResponse;
import com.everyones.lawmaking.domain.entity.Provider;
import com.everyones.lawmaking.global.config.OAuthConfig.KakaoClientProperties;
import com.everyones.lawmaking.repository.OAuth2ClientTokenRepository;
import java.net.URI;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

@Service
public class KakaoOAuthService extends OAuthService {
    private final KakaoClientProperties properties;
    private final RestTemplate restTemplate;

    @Autowired
    public KakaoOAuthService(OAuth2ClientTokenRepository oAuth2ClientTokenRepository, RestTemplate restTemplate, KakaoClientProperties properties) {
        super(oAuth2ClientTokenRepository);
        this.restTemplate = restTemplate;
        this.properties = properties;
    }

    @Override
    public Provider getProvider() {
        return properties.getProvider();
    }

    @Override
    public ResponseEntity<OAuthTokenResponse> getOAuthTokenResponse(Provider provider, String socialId){
        var recentSavedRefreshToken = super.getRecentSavedRefreshToken(provider, socialId);

        // Body 데이터
        MultiValueMap<String, String> requestData = new LinkedMultiValueMap<>();
        requestData.add("grant_type", "refresh_token");
        requestData.add("client_id", properties.getClientId());
        requestData.add("refresh_token", recentSavedRefreshToken);
        requestData.add("client_secret", properties.getClientSecret());

        // 헤더 설정
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        var uri = properties.getOAuthTokenUri();
        var requestEntity = new HttpEntity<>(requestData, headers);
        var oauthTokenResponse = restTemplate.postForEntity(uri, requestEntity, OAuthTokenResponse.class);
        return ResponseEntity.ok(oauthTokenResponse.getBody());
    }
    @Override
    public void unlink(Provider provider, String accessToken) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(accessToken);
        var requestEntity = new HttpEntity<>(headers);
        URI uri = properties.getUnlinkUri();
        restTemplate.postForEntity(uri, requestEntity, String.class);
    }
}
