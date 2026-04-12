package com.everyones.lawmaking.service.election.feed;

import com.everyones.lawmaking.common.dto.response.election.ElectionFeedItem;

import java.util.List;

public interface ElectionFeedProvider {

    String getType();

    /**
     * 피드 아이템을 커서 기반으로 조회합니다.
     *
     * @param electionId  선거 ID (예: "20260603")
     * @param cursorDate  커서 기준 publishedAt (null이면 최신부터 조회)
     * @param cursorId    커서 기준 아이템 ID (null이면 최신부터 조회)
     * @param limit       가져올 최대 아이템 수
     * @param party       정당 필터 (null이면 전체)
     * @param regionCode  지역 필터 (null이면 전체)
     * @return 정렬된 피드 아이템 목록
     */
    List<ElectionFeedItem> fetch(String electionId, String cursorDate, String cursorId,
                                  int limit, String party, String regionCode);
}
