package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.BillLike;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface BillLikeRepository extends JpaRepository<BillLike, Long > {

    @Query("select bl from BillLike bl " +
            "where bl.bill.id = :billId AND bl.user.id = :userId")
    Optional<BillLike> findByUserIdAndBillId(@Param("userId") long userId, @Param("billId") String billId);

    Long countByUserId(long userId);

    @Modifying(clearAutomatically = true)
    void deleteAllByUserId(Long userId);


}
