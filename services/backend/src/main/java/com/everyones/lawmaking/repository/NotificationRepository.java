package com.everyones.lawmaking.repository;


import com.everyones.lawmaking.domain.entity.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface NotificationRepository extends JpaRepository<Notification, Long> {

    @Query("""
            select n
            from Notification n
            Join n.user u
            where u.id = :userId and n.isRead = false
            order by n.createdDate desc
            """)
    List<Notification> findAllUnreadNotificationsByUserId(@Param("userId") Long userId);

    @Query("""
            select n
            from Notification n
            join n.user u
            where u.id = :userId and n.isRead = false
            order by n.createdDate desc
            limit 3
            """)
    List<Notification> findTop3UnreadNotificationsByUserIdSorted(@Param("userId") Long userId);
    @Query("""
            select n
            from Notification n
            Join n.user u
            where u.id = :userId
            order by n.createdDate desc
            """)
    List<Notification> findAllNotificationsByUserIdSorted(@Param("userId") Long userId);

    @Query("""
            select n
            from Notification n
            Join n.user u
            where u.id = :userId
            """)
    List<Notification> findAllNotificationsByUser(@Param("userId") Long userId);

    @Query("""
            select n
            from Notification n
            Join n.user u
            where u.id = :userId and n.id =:notificationId
            """)
    Optional<Notification> findNotificationByUserId(@Param("userId") Long userId, @Param("notificationId") int notificationId);

    @Query("""
            select n
            from Notification n
            Join n.user u
            where u.id = :userId and n.id =:notificationId and n.isRead = false
            """)
    Optional<Notification> findUnreadNotificationByUserId(@Param("userId") Long userId, @Param("notificationId") int notificationId);

    @Query("""
            select count(n)
            from Notification n
            Join n.user u
            where u.id = :userId and n.isRead = false
            """)
    Integer countNewNotificationsByUserId(Long userId);

    @Modifying(clearAutomatically = true)
    void deleteAllByUserId(Long userId);


}
