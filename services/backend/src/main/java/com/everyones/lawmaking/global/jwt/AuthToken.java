package com.everyones.lawmaking.global.jwt;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.security.Key;
import java.util.Date;

@Slf4j
@Getter
@RequiredArgsConstructor
public class AuthToken {

    private final String token;
    private final Key key;

    private static final String EMAIL_KEY = "email";

    private static final String AUTHENTICATION_KEY = "role";

    private static final String LOCAL_USER_ID = "userId";

    private static final String PROVIDER = "provider";



    AuthToken(Long userId,String role, Date expiry, Key key) {
        this.key = key;
        this.token = createAccessToken(userId,role, expiry);
    }

    AuthToken(Date expiry, Key key) {
        this.key = key;
        this.token = createRefreshToken(expiry);
    }
    // access Token 발급
    private String createAccessToken(Long userId,String role, Date expiry) {
        return Jwts.builder()
                .setSubject(userId.toString())
                .claim(AUTHENTICATION_KEY,role)
                .signWith(key, SignatureAlgorithm.HS256)
                .setExpiration(expiry)
                .compact();
    }

    // refresh Token 발급
    private String createRefreshToken(Date expiry) {
        return Jwts.builder()
                .signWith(key, SignatureAlgorithm.HS256)
                .setExpiration(expiry)
                .compact();
    }



    public boolean validate()  {
        return this.token != null && this.getTokenClaims() != null;
    }

    // ToDo(Exception 처리해야함)
    public Claims getTokenClaims() {
            return Jwts.parserBuilder()
                    .setSigningKey(key)
                    .build()
                    .parseClaimsJws(token)
                    .getBody();
        }


}
