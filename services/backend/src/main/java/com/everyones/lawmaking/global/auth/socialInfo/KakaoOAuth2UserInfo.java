package com.everyones.lawmaking.global.auth.socialInfo;

import lombok.extern.slf4j.Slf4j;

import java.util.Map;

@Slf4j
public class KakaoOAuth2UserInfo implements OAuth2UserInfo {

    private final Map<String, Object> attributes;

    public KakaoOAuth2UserInfo(Map<String, Object> attributes) {
        this.attributes = attributes;
    }

    @Override
    public String getId() {
        return getProperty("id");
    }

    @Override
    public String getName() {
        return getProperty("properties", "nickname");
    }

    @Override
    public String getEmail() {
        return getProperty("kakao_account", "email");
    }

    @Override
    public String getImageUrl() {
        return getProperty("properties", "profile_image");
    }

    private String getProperty(String top) {
        return String.valueOf(attributes.get(top));
    }

    private String getProperty(String top, String second) {
        var target = (Map<String, Object>) attributes.get(top);
        return String.valueOf(target.get(second));
    }

}
