package com.everyones.lawmaking.service.election.feed;

import com.everyones.lawmaking.common.dto.response.election.ElectionFeedItem;
import com.everyones.lawmaking.common.dto.response.election.feed.NewsFeedPayload;
import com.everyones.lawmaking.domain.entity.election.ElectionNews;
import com.everyones.lawmaking.repository.election.ElectionNewsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

@Component
@RequiredArgsConstructor
public class ElectionFeedNewsProvider implements ElectionFeedProvider {

    private final ElectionNewsRepository electionNewsRepository;

    @Override
    public String getType() {
        return "news";
    }

    @Override
    public List<ElectionFeedItem> fetch(String electionId, String cursorDate, String cursorId,
                                        int limit, String party, String regionCode) {
        PageRequest page = PageRequest.of(0, limit);
        List<ElectionNews> rows;

        if (cursorDate == null || cursorDate.isBlank()) {
            rows = electionNewsRepository.findFeedItemsFirst(electionId, page);
        } else {
            LocalDateTime dt = LocalDateTime.parse(
                    cursorDate.substring(0, 19), DateTimeFormatter.ISO_LOCAL_DATE_TIME);
            long id = Long.parseLong(cursorId);
            rows = electionNewsRepository.findFeedItems(electionId, dt, id, page);
        }

        return rows.stream()
                .map(n -> ElectionFeedItem.of(
                        "news-" + n.getId(),
                        getType(),
                        n.getPubDate().format(DateTimeFormatter.ISO_DATE_TIME),
                        NewsFeedPayload.from(n)))
                .toList();
    }
}
