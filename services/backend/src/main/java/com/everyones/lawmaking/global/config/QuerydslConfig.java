package com.everyones.lawmaking.global.config;

import com.querydsl.jpa.JPQLTemplates;
import com.querydsl.jpa.impl.JPAQueryFactory;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

/**
 * QueryDSLConfig class
 * @see <a href = "https://velog.io/@power0080/series/%EA%B9%80%EC%98%81%ED%95%9C%EC%8B%A4%EC%A0%84querydsl">블로그</a>
 * @see <a href = "http://querydsl.com/static/querydsl/3.6.3/reference/ko-KR/html_single/">QueryDSL 공식 문서</a>
 */
@Configuration
public class QuerydslConfig {
    @PersistenceContext
    private EntityManager entityManager;

    @Bean
    public JPAQueryFactory jpaQueryFactory() {
        return new JPAQueryFactory(JPQLTemplates.DEFAULT, entityManager);
    }
}