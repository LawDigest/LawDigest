package com.everyones.lawmaking.domain.entity;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import lombok.*;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.security.oauth2.core.OAuth2RefreshToken;

import java.time.Instant;
import java.util.Objects;

@Entity
@Builder
@Getter
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class SocialToken extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String clientRegistrationId;
    private String principalName;
    private String accessToken;
    private Instant accessTokenIssuedAt;
    private Instant accessTokenExpiresAt;
    private String refreshToken;
    private Instant refreshTokenIssuedAt;

    public static SocialToken from(OAuth2AuthorizedClient authorizedClient, Authentication principal){
        OAuth2AccessToken accessToken = authorizedClient.getAccessToken();
        OAuth2RefreshToken refreshToken = authorizedClient.getRefreshToken();
        return SocialToken.builder().accessToken(accessToken.getTokenValue())
                .accessTokenExpiresAt(Objects.requireNonNull(accessToken.getExpiresAt()))
                .accessTokenIssuedAt(Objects.requireNonNull(accessToken.getIssuedAt()))
                .clientRegistrationId(authorizedClient.getClientRegistration().getRegistrationId())
                .principalName(principal.getName())
                .refreshToken(Objects.requireNonNull(refreshToken).getTokenValue())
                .refreshTokenIssuedAt(Objects.requireNonNull(refreshToken.getIssuedAt()))
                .build();


    }
}
