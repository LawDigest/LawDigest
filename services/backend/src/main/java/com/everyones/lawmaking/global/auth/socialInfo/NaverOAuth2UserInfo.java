package com.everyones.lawmaking.global.auth.socialInfo;

import java.util.Map;

public class NaverOAuth2UserInfo implements OAuth2UserInfo {

    private Map<String, Object> attributes;

    public NaverOAuth2UserInfo(Map<String, Object> attributes) {
        this.attributes = attributes;
    }


    @Override
    public String getId() {
        return getProperty("id");
    }

    @Override
    public String getName() {
        return getProperty("nickname");
    }

    @Override
    public String getEmail() {
        return getProperty("email");
    }

    @Override
    public String getImageUrl() {
        return getProperty("profile_image");
    }

    private String getProperty(String key) {
        var response = (Map<String, Object>) attributes.get("response");
        return String.valueOf(response.get(key));
    }
}