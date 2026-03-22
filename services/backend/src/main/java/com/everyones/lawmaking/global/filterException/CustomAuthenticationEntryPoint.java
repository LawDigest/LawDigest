package com.everyones.lawmaking.global.filterException;

import io.jsonwebtoken.ExpiredJwtException;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;

import java.io.IOException;

@Slf4j
public class CustomAuthenticationEntryPoint implements AuthenticationEntryPoint {
    @Override
    public void commence(
            HttpServletRequest request,
            HttpServletResponse response,
            AuthenticationException authException
    ) throws IOException, ServletException {
        ExpiredJwtException ex = (ExpiredJwtException) request.getAttribute("expiredJwtException");
        if (ex != null) {
            // 특정 예외에 대한 처리 로직
            response.setContentType("application/json;charset=UTF-8");
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.getWriter().write("{\"reason\":\"The accessToken expired\"}");
        } else {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED,
                    authException.getLocalizedMessage());
        }
    }
}
