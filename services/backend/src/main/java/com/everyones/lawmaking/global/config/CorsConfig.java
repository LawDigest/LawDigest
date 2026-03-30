package com.everyones.lawmaking.global.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.Arrays;
import java.util.List;

@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Bean
    public UrlBasedCorsConfigurationSource corsConfigurationSource() {

        var source = new UrlBasedCorsConfigurationSource();
        var config = new CorsConfiguration();

        config.setAllowedHeaders(List.of("*"));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"));
        config.setAllowCredentials(true);
        config.setMaxAge(3600L);

        config.setAllowedOriginPatterns(List.of(
                "http://localhost:*",
                "https://localhost:*",
                "http://localhost.lawdigest.net:*",
                "https://localhost.lawdigest.net:*",
                "https://lawdigest.net",
                "https://www.lawdigest.net",
                "https://api.lawdigest.net",
                "https://dev.lawdigest.net",
                "https://*.lawdigest.net",
                "https://law-digest-fe-test.vercel.app",
                "https://test.lawdigest.cloud",
                "https://*.lawdigest.cloud"
        ));

        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
