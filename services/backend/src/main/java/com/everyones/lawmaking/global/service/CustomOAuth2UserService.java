package com.everyones.lawmaking.global.service;

import com.everyones.lawmaking.domain.entity.AuthInfo;
import com.everyones.lawmaking.domain.entity.Provider;
import com.everyones.lawmaking.domain.entity.Role;
import com.everyones.lawmaking.domain.entity.User;
import com.everyones.lawmaking.global.auth.PrincipalDetails;
import com.everyones.lawmaking.global.auth.socialInfo.OAuth2UserInfo;
import com.everyones.lawmaking.global.auth.socialInfo.OAuth2UserInfoFactory;
import com.everyones.lawmaking.repository.AuthInfoRepository;
import com.everyones.lawmaking.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.InternalAuthenticationServiceException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final AuthInfoRepository authInfoRepository;
    private final UserRepository userRepository;



    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User user = super.loadUser(userRequest);

        try {
            return this.process(userRequest, user);
        } catch (AuthenticationException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new InternalAuthenticationServiceException(ex.getMessage());
        }
    }

    private OAuth2User process(OAuth2UserRequest userRequest, OAuth2User user) {

        var provider = Provider.valueOf(userRequest.getClientRegistration().getRegistrationId().toUpperCase());

        // 소셜로그인에서 사용자 정보를 가져왔음
        var userInfo = OAuth2UserInfoFactory.getOAuth2UserInfo(provider, user.getAttributes());

        var userSocialId = userInfo.getId();
        // 저장된 AuthInfo 찾아서 값이 있으면 우리가 찾는 사용자인지 확인

        // 저장된 AuthInfo 으로 사용자 객체 들고옴
        var savedUser = userRepository.findBySocialIdAndProvider(userSocialId, provider)
                //TODO: 글로벌 익셉션으로 관리하기 현재는 401 에러
                .orElseGet(() -> createAuthAndUser(userInfo,provider));
        return PrincipalDetails.create(savedUser, userSocialId, provider, user.getAttributes());


    }

    private User createAuthAndUser(OAuth2UserInfo userInfo, Provider provider) {
        // AuthInfo에 데이터 저장
        AuthInfo authInfo = AuthInfo.builder()
                .socialId(userInfo.getId())
                .provider(provider)
                .build();
        authInfoRepository.save(authInfo);
        // User에 데이터 저장
        User user = User.builder()
                .authInfo(authInfo)
                .email(userInfo.getEmail())
                .imageUrl(userInfo.getImageUrl())
                .name(userInfo.getName())
                .role(Role.MEMBER)
                .build();
        userRepository.save(user);


        return user;

    }
}