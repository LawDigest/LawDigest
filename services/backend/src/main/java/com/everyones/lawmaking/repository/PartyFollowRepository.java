package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.PartyFollow;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface PartyFollowRepository extends JpaRepository<PartyFollow, Long> {

    @Query("select pf from PartyFollow pf " +
            "where pf.party.id = :partyId AND pf.user.id = :userId ")
    Optional<PartyFollow> findByUserIdAndPartyId(@Param("userId") long userId, @Param("partyId") long partyId);

    @Modifying(clearAutomatically = true)
    void deleteAllByUserId(Long userId);
}
