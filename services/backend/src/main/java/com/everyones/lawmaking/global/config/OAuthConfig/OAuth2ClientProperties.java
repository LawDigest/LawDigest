package com.everyones.lawmaking.global.config.OAuthConfig;

import com.everyones.lawmaking.domain.entity.Provider;
import java.net.URI;
import org.springframework.http.HttpEntity;

public interface OAuth2ClientProperties {

    Provider getProvider();

    String getClientId();

    String getClientSecret();

    URI getOAuthTokenUri();

    URI getUnlinkUri();


}
