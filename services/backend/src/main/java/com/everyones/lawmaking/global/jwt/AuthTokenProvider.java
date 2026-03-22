package com.everyones.lawmaking.global.jwt;


import com.everyones.lawmaking.domain.entity.Role;
import com.everyones.lawmaking.global.config.OAuthConfig.AppProperties;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import java.security.Key;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Date;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthTokenProvider {

    private static final String LOCAL_USER_ID = "userId";
    private final Key key;
    private static final String AUTHORITIES_KEY = "role";

    private final AppProperties appProperties;

    @Autowired
    public AuthTokenProvider(AppProperties appProperties) {
        this.appProperties = appProperties;
        this.key = Keys.hmacShaKeyFor(this.appProperties.getTokenSecret().getBytes());
    }

    public AuthToken createAuthToken(Date expiry) {
        return new AuthToken(expiry, key);
    }

    public AuthToken createAuthToken(Long userId,String role, Date expiry) {
        return new AuthToken(userId,role, expiry, key);
    }

    public AuthToken convertAuthToken(String token) {
        return new AuthToken(token, key);
    }

    public Authentication getAuthentication(AuthToken authToken) {

        if (authToken.validate()) {

            var claims = authToken.getTokenClaims();
            Collection<? extends GrantedAuthority> authorities;
            if (claims.get(AUTHORITIES_KEY) != null){
                authorities =
                        Arrays.stream(new String[]{claims.get(AUTHORITIES_KEY).toString()})
                                .map(SimpleGrantedAuthority::new)
                                .collect(Collectors.toList());
                // 비밀번호 사용되지 않음

                UserDetails principal = new User(claims.getSubject(), "", authorities);
                return new UsernamePasswordAuthenticationToken(principal, authToken, authorities);
            }
            // 클레임에 권한이 null인 경우
            else{
                var guestAuthority = new SimpleGrantedAuthority(Role.GUEST.getCode());
                authorities = Collections.singleton(guestAuthority);
                // 비밀번호 사용되지 않음
                UserDetails principal = new User("anonymous", "", authorities);
                return new UsernamePasswordAuthenticationToken(principal, null, authorities);
            }
        // 토큰이 검증이 되지 않았을 경우는 게스트를 가진 권한을 부여하게 된다.
        } else {
            var guestAuthority = new SimpleGrantedAuthority(Role.GUEST.getCode());
            Collection<? extends GrantedAuthority> authorities = Collections.singleton(guestAuthority);
            // 비밀번호 사용되지 않음
            UserDetails principal = new User("anonymous", "", authorities);
            return new UsernamePasswordAuthenticationToken(principal, null, authorities);
        }
    }

}

