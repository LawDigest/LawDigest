package com.everyones.lawmaking.service.election.feed;

import com.everyones.lawmaking.common.dto.response.election.ElectionFeedItem;
import com.everyones.lawmaking.common.dto.response.election.feed.ScheduleFeedPayload;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class ElectionFeedScheduleProvider implements ElectionFeedProvider {

    private final ObjectMapper objectMapper;
    private List<ScheduleEvent> scheduleEvents = List.of();

    @PostConstruct
    void loadSchedule() {
        try {
            var resource = new ClassPathResource("data/schedule_local_2026.json");
            scheduleEvents = objectMapper.readValue(
                    resource.getInputStream(),
                    new TypeReference<List<ScheduleEvent>>() {}
            );
            log.info("선거 일정 {}건 로드 완료", scheduleEvents.size());
        } catch (IOException e) {
            log.error("선거 일정 JSON 로드 실패: {}", e.getMessage());
        }
    }

    @Override
    public String getType() {
        return "schedule";
    }

    @Override
    public List<ElectionFeedItem> fetch(String electionId, String cursorDate, String cursorId,
                                         int limit, String party, String regionCode) {
        return scheduleEvents.stream()
                .filter(e -> electionId == null || electionId.equals(e.getElectionId()))
                .sorted(Comparator.comparing(ScheduleEvent::getEventDate).reversed()
                        .thenComparing(Comparator.comparing(ScheduleEvent::getId).reversed()))
                .filter(e -> {
                    if (cursorDate == null || cursorId == null) return true;
                    String eventPublishedAt = e.getEventDate().atStartOfDay()
                            .format(DateTimeFormatter.ISO_DATE_TIME);
                    int dateCmp = eventPublishedAt.compareTo(cursorDate);
                    if (dateCmp < 0) return true;
                    if (dateCmp == 0) return e.getId().compareTo(cursorId) < 0;
                    return false;
                })
                .limit(limit)
                .map(e -> ElectionFeedItem.of(
                        e.getId(),
                        getType(),
                        e.getEventDate().atStartOfDay().format(DateTimeFormatter.ISO_DATE_TIME),
                        ScheduleFeedPayload.of(e.getTitle(), e.getDescription(),
                                e.getEventDate().toString(), e.getEventType())
                ))
                .toList();
    }

    @Getter
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ScheduleEvent {
        private String id;
        @JsonProperty("electionId")
        private String electionId;
        private String title;
        private String description;
        @JsonProperty("eventDate")
        private LocalDate eventDate;
        @JsonProperty("eventType")
        private String eventType;
    }
}
