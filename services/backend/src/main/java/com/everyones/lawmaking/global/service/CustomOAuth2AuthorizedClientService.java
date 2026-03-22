package com.everyones.lawmaking.global.service;

import com.everyones.lawmaking.domain.entity.SocialToken;
import com.everyones.lawmaking.repository.OAuth2ClientTokenRepository;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.security.oauth2.core.OAuth2RefreshToken;

import java.util.Optional;

public class CustomOAuth2AuthorizedClientService implements OAuth2AuthorizedClientService {
    private final OAuth2ClientTokenRepository clientTokenRepository; // OAuth2 클라이언트 정보 저장소 (데이터베이스 연동용)
    private final ClientRegistrationRepository clientRegistrationRepository;


    public CustomOAuth2AuthorizedClientService(OAuth2ClientTokenRepository clientTokenRepository,
                                               ClientRegistrationRepository clientRegistrationRepository) {
        this.clientTokenRepository = clientTokenRepository;
        this.clientRegistrationRepository = clientRegistrationRepository;
    }

    @Override
    @SuppressWarnings("unchecked")
    public <T extends OAuth2AuthorizedClient> T loadAuthorizedClient(String clientRegistrationId, String principalName) {
        Optional<SocialToken> clientEntity = clientTokenRepository.findTop1ByClientRegistrationIdAndPrincipalNameOrderByCreatedDateDesc(clientRegistrationId, principalName);
        try {
            if (clientEntity.isPresent()) {
                SocialToken socialToken = clientEntity.get();
                ClientRegistration registration = clientRegistrationRepository.findByRegistrationId(clientRegistrationId);
                OAuth2AccessToken accessToken = new OAuth2AccessToken(
                        OAuth2AccessToken.TokenType.BEARER,
                        socialToken.getAccessToken(),
                        socialToken.getAccessTokenIssuedAt(),
                        socialToken.getAccessTokenExpiresAt()
                );
                OAuth2RefreshToken refreshToken = new OAuth2RefreshToken(
                        socialToken.getRefreshToken(),
                        socialToken.getRefreshTokenIssuedAt()
                );

                return (T) new OAuth2AuthorizedClient(registration, principalName, accessToken, refreshToken);
            }
        } catch (RuntimeException e) {
            throw new RuntimeException( e.getMessage(), e.getCause());
        }


        return null;
    }

    @Override
    public void saveAuthorizedClient(OAuth2AuthorizedClient authorizedClient, Authentication principal) {
        SocialToken clientEntity = SocialToken.from(authorizedClient, principal);

        clientTokenRepository.save(clientEntity); // 데이터베이스에 저장
    }

    @Override
    public void removeAuthorizedClient(String clientRegistrationId, String principalName) {
        clientTokenRepository.deleteByClientRegistrationIdAndPrincipalName(clientRegistrationId, principalName);
    }
}

