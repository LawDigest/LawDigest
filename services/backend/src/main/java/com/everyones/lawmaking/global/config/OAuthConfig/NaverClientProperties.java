package com.everyones.lawmaking.global.config.OAuthConfig;

import com.everyones.lawmaking.domain.entity.Provider;
import java.net.URI;
import lombok.Getter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.util.UriComponentsBuilder;

@Getter
@Component
public class NaverClientProperties implements OAuth2ClientProperties{
    @Value("${app.auth.naver-app-client-id}")
    private String clientId;
    @Value("${app.auth.naver-app-client-secret}")
    private String clientSecret;

    @Override
    public Provider getProvider() {
        return Provider.NAVER;
    }

    @Override
    public URI getOAuthTokenUri() {
        return UriComponentsBuilder
                .fromUriString("https://nid.naver.com")
                .path("/oauth2.0/token")
                .encode()
                .build()
                .toUri();
    }

    @Override
    public URI getUnlinkUri() {
        return UriComponentsBuilder
                .fromUriString("https://nid.naver.com")
                .path("/oauth2.0/token")
                .encode()
                .build()
                .toUri();
    }
}
