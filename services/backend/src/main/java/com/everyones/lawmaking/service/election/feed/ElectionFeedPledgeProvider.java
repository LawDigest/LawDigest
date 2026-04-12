package com.everyones.lawmaking.service.election.feed;

import com.everyones.lawmaking.common.dto.response.election.ElectionFeedItem;
import com.everyones.lawmaking.common.dto.response.election.feed.PledgeFeedPayload;
import com.everyones.lawmaking.domain.entity.election.ElectionPledge;
import com.everyones.lawmaking.repository.election.ElectionPledgeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

@Component
@RequiredArgsConstructor
public class ElectionFeedPledgeProvider implements ElectionFeedProvider {

    private final ElectionPledgeRepository pledgeRepository;

    @Override
    public String getType() {
        return "pledge";
    }

    @Override
    public List<ElectionFeedItem> fetch(String electionId, String cursorDate, String cursorId,
                                         int limit, String party, String regionCode) {
        List<ElectionPledge> pledges;
        PageRequest page = PageRequest.of(0, limit);

        if (cursorDate == null || cursorId == null) {
            pledges = pledgeRepository.findFeedItemsFirst(electionId, page);
        } else {
            LocalDateTime parsedDate = LocalDateTime.parse(cursorDate, DateTimeFormatter.ISO_DATE_TIME);
            long parsedId = Long.parseLong(cursorId);
            pledges = pledgeRepository.findFeedItems(electionId, parsedDate, parsedId, page);
        }

        return pledges.stream()
                .map(pledge -> ElectionFeedItem.of(
                        "pledge-" + pledge.getId(),
                        getType(),
                        pledge.getCreatedAt() != null
                                ? pledge.getCreatedAt().format(DateTimeFormatter.ISO_DATE_TIME)
                                : pledge.getUpdatedAt().format(DateTimeFormatter.ISO_DATE_TIME),
                        PledgeFeedPayload.from(pledge)
                ))
                .toList();
    }
}
