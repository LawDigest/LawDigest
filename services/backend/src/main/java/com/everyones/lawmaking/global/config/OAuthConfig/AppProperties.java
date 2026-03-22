package com.everyones.lawmaking.global.config.OAuthConfig;

import java.util.List;
import lombok.Getter;
import lombok.Setter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
public class AppProperties {
    @Value("${app.auth.token-secret}")
    private String tokenSecret;
    @Value("${app.auth.cookie-domain}")
    private String cookieDomain;
    @Value("${app.oauth2.client-redirect-uri}")
    private List<String> oauth2ClientRedirectUri;
    @Value("${app.auth.access-token-expiry}")
    private long accessTokenExpiry;
    @Value("${app.auth.refresh-token-expiry}")
    private long refreshTokenExpiry;

}
