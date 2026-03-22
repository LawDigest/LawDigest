package com.everyones.lawmaking.global.auth.socialInfo;

import lombok.extern.slf4j.Slf4j;

import java.util.Map;

@Slf4j
public class GoogleOAuth2UserInfo implements OAuth2UserInfo {

    private final Map<String, Object> attributes;

    public GoogleOAuth2UserInfo(Map<String, Object> attributes) {
        this.attributes = attributes;
    }

    @Override
    public String getId() {
        return getProperty("sub");
    }

    @Override
    public String getName() {
        return getProperty("name");
    }

    @Override
    public String getEmail() {
        return getProperty("email");
    }

    @Override
    public String getImageUrl() {
        return getProperty("picture");
    }

    private String getProperty(String key) {
        return String.valueOf(attributes.get(key));
    }
} 