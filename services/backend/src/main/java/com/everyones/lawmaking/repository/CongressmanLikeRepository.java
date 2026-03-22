package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.CongressmanLike;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CongressmanLikeRepository extends JpaRepository<CongressmanLike, Long> {

    @Query("SELECT cl FROM CongressmanLike cl " +
            "WHERE cl.user.id = :userId AND cl.congressman.id = :congressmanId")
    Optional<CongressmanLike> findByUserIdAndCongressmanId(@Param("userId")long userId, @Param("congressmanId")String congressmanId);


    Long countByUserId(long userId);

    Long countByCongressmanId(String congressmanId);

    @Modifying(clearAutomatically = true)
    void deleteByUserId(Long userId);



}
