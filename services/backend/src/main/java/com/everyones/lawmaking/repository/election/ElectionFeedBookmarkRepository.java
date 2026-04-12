package com.everyones.lawmaking.repository.election;

import com.everyones.lawmaking.domain.entity.election.ElectionFeedBookmark;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ElectionFeedBookmarkRepository extends JpaRepository<ElectionFeedBookmark, Long> {

    Optional<ElectionFeedBookmark> findByUser_IdAndFeedTypeAndFeedItemId(
            long userId, String feedType, String feedItemId);

    boolean existsByUser_IdAndFeedTypeAndFeedItemId(
            long userId, String feedType, String feedItemId);
}
