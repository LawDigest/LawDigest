package com.everyones.lawmaking.global.auth.socialInfo;

import com.everyones.lawmaking.domain.entity.Provider;
import lombok.extern.slf4j.Slf4j;

import java.util.Map;
import java.util.Objects;

import static com.everyones.lawmaking.domain.entity.Provider.*;


@Slf4j
public class OAuth2UserInfoFactory {
    public static OAuth2UserInfo getOAuth2UserInfo(Provider provider, Map<String, Object> attributes) {
        if (Objects.requireNonNull(provider) == KAKAO) {
            return new KakaoOAuth2UserInfo(attributes);
        } else if (Objects.requireNonNull(provider) == NAVER) {
            return new NaverOAuth2UserInfo(attributes);
        } else if (Objects.requireNonNull(provider) == GOOGLE) {
            return new GoogleOAuth2UserInfo(attributes);
        }
        throw new IllegalArgumentException("유효하지 않은 Provider Type 입니다.");
    }

}
