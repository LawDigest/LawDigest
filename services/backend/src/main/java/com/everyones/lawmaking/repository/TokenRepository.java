package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.Token;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

public interface TokenRepository extends JpaRepository<Token, Long> {



    @Query("select t " +
            "from Token t " +
            "inner join fetch t.user u " +
            "where t.refreshToken =:refreshToken ")
    Optional<Token> findTokenByRefreshToken(@Param("refreshToken") String refreshToken);

    @Modifying(clearAutomatically = true)
    Integer deleteByUserId(Long userId);


}
