package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.OAuthTokenResponse;
import com.everyones.lawmaking.domain.entity.Provider;
import com.everyones.lawmaking.global.config.OAuthConfig.NaverClientProperties;
import com.everyones.lawmaking.repository.OAuth2ClientTokenRepository;
import java.net.URI;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Service
public class NaverOAuthService extends OAuthService {
    private final NaverClientProperties properties;
    private final RestTemplate restTemplate;

    @Autowired
    public NaverOAuthService(OAuth2ClientTokenRepository oAuth2ClientTokenRepository, NaverClientProperties properties, RestTemplate restTemplate) {
        super(oAuth2ClientTokenRepository);
        this.properties = properties;
        this.restTemplate = restTemplate;
    }

    @Override
    public Provider getProvider() {
        return properties.getProvider();
    }

    @Override
    public ResponseEntity<OAuthTokenResponse> getOAuthTokenResponse(Provider provider, String socialId) {
        var recentSavedRefreshToken = super.getRecentSavedRefreshToken(provider, socialId);
        MultiValueMap<String, String> requestParams = new LinkedMultiValueMap<>();
        requestParams.add("client_id", properties.getClientId());
        requestParams.add("client_secret", properties.getClientSecret());
        requestParams.add("grant_type", "refresh_token");
        requestParams.add("refresh_token", recentSavedRefreshToken);
        var uri = UriComponentsBuilder.fromUri(properties.getOAuthTokenUri())
                .queryParams(requestParams)
                .build()
                .toUri();
        var oauthTokenResponse = restTemplate.postForEntity(uri, null, OAuthTokenResponse.class);

        return ResponseEntity.ok(oauthTokenResponse.getBody());
    }

    @Override
    public void unlink(Provider provider, String accessToken) {
        MultiValueMap<String, String> requestParams = new LinkedMultiValueMap<>();
        requestParams.add("client_id", properties.getClientId());
        requestParams.add("client_secret", properties.getClientSecret());
        requestParams.add("access_token", accessToken);
        requestParams.add("grant_type", "delete");
        requestParams.add("service_provider", "NAVER");

        URI uri = UriComponentsBuilder.fromUri(properties.getUnlinkUri())
                .queryParams(requestParams)
                .build()
                .toUri();
        restTemplate.postForEntity(uri, null, String.class);
    }
}
