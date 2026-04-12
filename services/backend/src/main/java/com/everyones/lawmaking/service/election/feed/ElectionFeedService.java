package com.everyones.lawmaking.service.election.feed;

import com.everyones.lawmaking.common.dto.response.election.ElectionFeedItem;
import com.everyones.lawmaking.common.dto.response.election.ElectionFeedResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ElectionFeedService {

    private static final int MAX_LIMIT = 50;

    private final List<ElectionFeedProvider> providers;

    public ElectionFeedResponse getFeed(String electionId, String cursor, int limit,
                                         String type, String party, String regionCode) {
        int safeLimit = Math.min(limit, MAX_LIMIT);
        int fetchSize = safeLimit + 1;

        String cursorDate = null;
        String cursorId = null;
        if (cursor != null && !cursor.isBlank()) {
            String decoded = new String(Base64.getDecoder().decode(cursor), StandardCharsets.UTF_8);
            int sep = decoded.indexOf('|');
            if (sep > 0) {
                cursorDate = decoded.substring(0, sep);
                cursorId = decoded.substring(sep + 1);
            }
        }

        final String finalCursorDate = cursorDate;
        final String finalCursorId = cursorId;

        List<ElectionFeedItem> merged = providers.stream()
                .filter(p -> type == null || type.isBlank() || "all".equalsIgnoreCase(type)
                        || p.getType().equalsIgnoreCase(type))
                .flatMap(p -> p.fetch(electionId, finalCursorDate, finalCursorId,
                        fetchSize, party, regionCode).stream())
                .sorted(Comparator.comparing(ElectionFeedItem::getPublishedAt,
                        Comparator.nullsLast(Comparator.reverseOrder())))
                .collect(Collectors.toList());

        boolean hasMore = merged.size() > safeLimit;
        List<ElectionFeedItem> items = hasMore ? merged.subList(0, safeLimit) : merged;

        String nextCursor = null;
        if (hasMore && !items.isEmpty()) {
            ElectionFeedItem last = items.get(items.size() - 1);
            String raw = last.getPublishedAt() + "|" + last.getId();
            nextCursor = Base64.getEncoder().encodeToString(raw.getBytes(StandardCharsets.UTF_8));
        }

        return ElectionFeedResponse.of(items, nextCursor, hasMore);
    }
}
