package com.everyones.lawmaking.global.config.OAuthConfig;

import com.everyones.lawmaking.domain.entity.Provider;
import com.everyones.lawmaking.service.OAuthService;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class OAuthServiceFactory {
    private final Map<Provider, OAuthService> oAuth2ClientPropertiesMap;

    @Autowired
    public OAuthServiceFactory(List<OAuthService> oAuth2ClientPropertiesList) {
        oAuth2ClientPropertiesMap = oAuth2ClientPropertiesList.stream()
                .collect(Collectors.toMap(OAuthService::getProvider, Function.identity()));
    }

    public OAuthService getOAuthService(Provider provider) {
        return oAuth2ClientPropertiesMap.get(provider);
    }
}
