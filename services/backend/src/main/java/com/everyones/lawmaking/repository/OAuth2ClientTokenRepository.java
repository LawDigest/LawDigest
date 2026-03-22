package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.SocialToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface OAuth2ClientTokenRepository extends JpaRepository<SocialToken, Long> {
    Optional<SocialToken> findTop1ByClientRegistrationIdAndPrincipalNameOrderByCreatedDateDesc(String clientRegistrationId,String principalName);
    void deleteByClientRegistrationIdAndPrincipalName(String clientRegistrationId, String principalName);

}
