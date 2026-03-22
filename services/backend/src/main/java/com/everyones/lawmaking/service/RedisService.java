package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.BillTimelineResponse;
import java.time.LocalDate;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class RedisService {

    private final RedisTemplate<String, Object> redisTemplate;

    private final String TIMELINE_KEY = "timelineQueue";
    private static final String LIKES_QUEUE = "likesQueue";
    private static final String VIEWS_QUEUE = "viewsQueue";

    private static final int LIKES_QUEUE_SIZE = 1000;
    private static final int VIEWS_QUEUE_SIZE = 3000;

    public boolean isTimelineCached(LocalDate localDate) {
        return Boolean.TRUE.equals(redisTemplate.hasKey(TIMELINE_KEY + localDate));
    }
    public BillTimelineResponse getTimelineCached(LocalDate localDate) {
        return (BillTimelineResponse) redisTemplate.opsForValue().get(TIMELINE_KEY + localDate);
    }


    // 인기글 조회
    public List<String> getPopularBills() {
        List<Object> likesList = getLikesQueue();
        List<Object> viewsList = getViewsQueue();

        Map<String, Integer> postScores = new HashMap<>();

        // 좋아요 큐의 점수 계산
        for (Object billId : likesList) {
            postScores.put(billId.toString(), postScores.getOrDefault(billId.toString(), 0) + 8);
        }

        // 조회수 큐의 점수 계산
        for (Object billId : viewsList) {
            postScores.put(billId.toString(), postScores.getOrDefault(billId.toString(), 0) + 2);
        }

        // 점수에 따라 상위 10개 추출
        return postScores.entrySet()
                .stream()
                .sorted(Collections.reverseOrder(Map.Entry.comparingByValue()))
                .limit(10)
                .map(Map.Entry::getKey)
                .toList();
    }

    // 좋아요 큐 삽입
    public void addToLikesQueue(String billId) {
        manageQueue(LIKES_QUEUE, billId, LIKES_QUEUE_SIZE);
    }

    // 조회수 큐 삽입
    public void addToViewsQueue(String billId) {
        manageQueue(VIEWS_QUEUE, billId, VIEWS_QUEUE_SIZE);
    }

    // 좋아요 또는 조회수 큐 삽입
    private void manageQueue(String queueName, String billId, int queueSize) {
        redisTemplate.opsForList().rightPush(queueName, billId);
        Long size = redisTemplate.opsForList().size(queueName);
        if (size != null && size > queueSize) {
            redisTemplate.opsForList().leftPop(queueName);
        }
    }

    public List<Object> getLikesQueue() {
        return redisTemplate.opsForList().range(LIKES_QUEUE, 0, -1);
    }

    public List<Object> getViewsQueue() {
        return redisTemplate.opsForList().range(VIEWS_QUEUE, 0, -1);
    }



    

}
