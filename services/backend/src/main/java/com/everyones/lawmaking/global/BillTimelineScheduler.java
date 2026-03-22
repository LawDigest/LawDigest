package com.everyones.lawmaking.global;

import com.everyones.lawmaking.common.dto.response.BillTimelineResponse;
import com.everyones.lawmaking.facade.BillFacade;
import com.everyones.lawmaking.facade.TimelineFacade;
import com.everyones.lawmaking.repository.BillTimelineRepository;
import java.time.LocalDate;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;

@RequiredArgsConstructor
public class BillTimelineScheduler {
    private final RedisTemplate<String, Object> redisTemplate;
    private final BillTimelineRepository billTimelineRepository;
    private final TimelineFacade timelineFacade;

    @Scheduled(cron = "0 0/30 8-19 * * MON-FRI")
    public void refreshTimelineCache() {
        LocalDate today = LocalDate.now();
        String TIMELINE_KEY = "timelineQueue";
        String todayKey = TIMELINE_KEY + today;
        LocalDate recentUpdateDate = billTimelineRepository.findTopByOrderByStatusUpdateDateDesc();
        // 오래된 데이터 제거
        LocalDate tenDaysAgo = today.minusDays(7);
        String oldestKey = TIMELINE_KEY + tenDaysAgo;
        redisTemplate.delete(oldestKey);

        // 업데이트 할 필요가 없다면 return
        boolean isUpdated = Boolean.TRUE.equals(redisTemplate.hasKey(todayKey));
        if (!today.equals(recentUpdateDate) || isUpdated) {
            return;
        }

        // 오늘 데이터 추가
        BillTimelineResponse billTimelineResponse = timelineFacade.getTimeline(today);
        redisTemplate.opsForValue().set(todayKey, billTimelineResponse);
    }
}
