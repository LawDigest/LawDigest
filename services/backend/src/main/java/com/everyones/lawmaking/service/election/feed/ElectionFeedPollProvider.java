package com.everyones.lawmaking.service.election.feed;

import com.everyones.lawmaking.common.dto.response.election.ElectionFeedItem;
import com.everyones.lawmaking.common.dto.response.election.feed.PollFeedPayload;
import com.everyones.lawmaking.domain.entity.poll.PollSurvey;
import com.everyones.lawmaking.repository.poll.PollSurveyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

@Component
@RequiredArgsConstructor
public class ElectionFeedPollProvider implements ElectionFeedProvider {

    private final PollSurveyRepository pollSurveyRepository;

    @Override
    public String getType() {
        return "poll";
    }

    @Override
    public List<ElectionFeedItem> fetch(String electionId, String cursorDate, String cursorId,
                                         int limit, String party, String regionCode) {
        List<PollSurvey> surveys;
        PageRequest page = PageRequest.of(0, limit);

        if (cursorDate == null || cursorId == null) {
            surveys = pollSurveyRepository.findFeedItemsFirst(page);
        } else {
            LocalDateTime parsedDate = LocalDateTime.parse(cursorDate, DateTimeFormatter.ISO_DATE_TIME);
            surveys = pollSurveyRepository.findFeedItems(parsedDate, cursorId, page);
        }

        return surveys.stream()
                .map(survey -> ElectionFeedItem.of(
                        "poll-" + survey.getRegistrationNumber(),
                        getType(),
                        survey.getCreatedDate() != null
                                ? survey.getCreatedDate().format(DateTimeFormatter.ISO_DATE_TIME)
                                : survey.getSurveyEndDate().atStartOfDay().format(DateTimeFormatter.ISO_DATE_TIME),
                        PollFeedPayload.from(survey)
                ))
                .toList();
    }
}
