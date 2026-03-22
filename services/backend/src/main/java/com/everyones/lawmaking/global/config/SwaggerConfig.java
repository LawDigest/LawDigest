package com.everyones.lawmaking.global.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springdoc.core.models.GroupedOpenApi;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Arrays;
import java.util.Collections;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI openAPI() {
        SecurityScheme securityScheme = new SecurityScheme()
                .type(SecurityScheme.Type.HTTP).scheme("bearer").bearerFormat("JWT")
                .in(SecurityScheme.In.HEADER).name("Authorization");
        SecurityRequirement securityRequirement = new SecurityRequirement().addList("bearer-token");


        return new OpenAPI()
                .components(new Components()
                .addSecuritySchemes("bearer-token",securityScheme))
                .security(Collections.singletonList(securityRequirement))
                .info(apiInfo());
    }

    @Bean
    public GroupedOpenApi allApi() {
        return GroupedOpenApi.builder()
                .group("All")
                .pathsToMatch("/v1/**")
                .build();
    }

    @Bean
    public GroupedOpenApi apiNeededAuthorization() {
        return GroupedOpenApi.builder()
                .group("Authorization")
                .pathsToMatch("/**/like**", "/**/bookmark**", "/**/follow**")
                .build();
    }



    private Info apiInfo() {
        return new Info()
                .title("LawDigest V1 API")
                .description("LawBag 명세 문서.")
                .version("1.0.0");
    }
}
