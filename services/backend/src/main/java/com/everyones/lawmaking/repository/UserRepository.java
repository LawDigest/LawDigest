package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.Provider;
import com.everyones.lawmaking.domain.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;


@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    @Query("select u " +
            "from User u " +
            "join fetch u.authInfo " +
            "where u.authInfo.socialId=:socialId and u.authInfo.provider =:provider")
    Optional<User> findBySocialIdAndProvider(@Param("socialId") String socialId, @Param("provider") Provider provider);

    @Query("select u " +
            "from User u " +
            "where u.authInfo.socialId=:socialId and u.authInfo.provider =:provider")
    Optional<User> findUserBySocialIdAndProvider(@Param("socialId") String socialId, @Param("provider") Provider provider);


    @Query("SELECT cl.user FROM CongressmanLike cl " +
            "WHERE cl.congressman.id = :congressmanId")
    List<User> findAllByCongressmanId(@Param("congressmanId") String congressmanId);

    @Query("select bl.user from BillLike bl " +
            "where bl.bill.id = :billId")
    List<User> findAllByBillId(@Param("billId") String billId);

    @Modifying(clearAutomatically = true)
    int deleteUserById(Long userId);
}
