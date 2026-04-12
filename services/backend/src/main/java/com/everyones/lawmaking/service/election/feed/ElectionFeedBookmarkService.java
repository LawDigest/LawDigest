package com.everyones.lawmaking.service.election.feed;

import com.everyones.lawmaking.domain.entity.User;
import com.everyones.lawmaking.domain.entity.election.ElectionFeedBookmark;
import com.everyones.lawmaking.global.error.AuthException;
import com.everyones.lawmaking.repository.UserRepository;
import com.everyones.lawmaking.repository.election.ElectionFeedBookmarkRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;

import static com.everyones.lawmaking.global.util.AuthenticationUtil.requireUserId;

@Service
@RequiredArgsConstructor
public class ElectionFeedBookmarkService {

    private final ElectionFeedBookmarkRepository bookmarkRepository;
    private final UserRepository userRepository;

    @Transactional
    public Map<String, Object> addBookmark(Authentication auth, String feedType, String feedItemId) {
        long userId = requireUserId(auth);
        boolean alreadyExists = bookmarkRepository.existsByUser_IdAndFeedTypeAndFeedItemId(
                userId, feedType, feedItemId);
        if (!alreadyExists) {
            User user = userRepository.findById(userId)
                    .orElseThrow(AuthException.Unauthorized::new);
            ElectionFeedBookmark bookmark = ElectionFeedBookmark.builder()
                    .user(user)
                    .feedType(feedType)
                    .feedItemId(feedItemId)
                    .build();
            bookmarkRepository.save(bookmark);
        }
        return Map.of("bookmarked", true, "feed_type", feedType, "feed_item_id", feedItemId);
    }

    @Transactional
    public Map<String, Object> removeBookmark(Authentication auth, String feedType, String feedItemId) {
        long userId = requireUserId(auth);
        bookmarkRepository.findByUser_IdAndFeedTypeAndFeedItemId(userId, feedType, feedItemId)
                .ifPresent(bookmarkRepository::delete);
        return Map.of("bookmarked", false, "feed_type", feedType, "feed_item_id", feedItemId);
    }

    @Transactional(readOnly = true)
    public Map<String, Object> getBookmarkStatus(Authentication auth, String feedType, String feedItemId) {
        long userId = requireUserId(auth);
        boolean bookmarked = bookmarkRepository.existsByUser_IdAndFeedTypeAndFeedItemId(
                userId, feedType, feedItemId);
        return Map.of("bookmarked", bookmarked, "feed_type", feedType, "feed_item_id", feedItemId);
    }
}
