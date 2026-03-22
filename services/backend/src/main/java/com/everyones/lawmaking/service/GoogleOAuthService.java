package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.OAuthTokenResponse;
import com.everyones.lawmaking.domain.entity.Provider;
import com.everyones.lawmaking.global.config.OAuthConfig.GoogleClientProperties;
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
import org.springframework.web.util.UriComponentsBuilder;

@Service
public class GoogleOAuthService extends OAuthService {

    private final GoogleClientProperties properties;
    private final RestTemplate restTemplate;

    @Autowired
    public GoogleOAuthService(OAuth2ClientTokenRepository oAuth2ClientTokenRepository, GoogleClientProperties properties, RestTemplate restTemplate) {
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
        MultiValueMap<String, String> requestBody = new LinkedMultiValueMap<>();
        requestBody.add("grant_type", "refresh_token");
        requestBody.add("client_id", properties.getClientId());
        requestBody.add("client_secret", properties.getClientSecret());
        requestBody.add("refresh_token", recentSavedRefreshToken);
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        var uri = properties.getOAuthTokenUri();
        var requestData = new HttpEntity<>(requestBody, headers);
        var oauthTokenResponse = restTemplate.postForEntity(uri, requestData, OAuthTokenResponse.class);
        return ResponseEntity.ok(oauthTokenResponse.getBody());
    }

    @Override
    public void unlink(Provider provider, String accessToken) {
        MultiValueMap<String, String> requestParams = new LinkedMultiValueMap<>();
        requestParams.add("token", accessToken);
        URI uri = UriComponentsBuilder.fromUri(properties.getUnlinkUri())
                .queryParams(requestParams)
                .build()
                .toUri();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        var requestEntity = new HttpEntity<>(headers);

        restTemplate.postForEntity(uri, requestEntity, String.class);
    }
}
