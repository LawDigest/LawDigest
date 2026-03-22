package com.everyones.lawmaking.global.config.OAuthConfig;

import com.everyones.lawmaking.domain.entity.Provider;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class OAuthPropertiesFactory {
    private final Map<Provider, OAuth2ClientProperties> oAuth2ClientPropertiesMap;

    @Autowired
    public OAuthPropertiesFactory(List<OAuth2ClientProperties> oAuth2ClientPropertiesList) {
        oAuth2ClientPropertiesMap = oAuth2ClientPropertiesList.stream()
                .collect(Collectors.toMap(OAuth2ClientProperties::getProvider, Function.identity()));
    }

    public OAuth2ClientProperties getClientProperties(Provider provider) {
        return oAuth2ClientPropertiesMap.get(provider);
    }
}
