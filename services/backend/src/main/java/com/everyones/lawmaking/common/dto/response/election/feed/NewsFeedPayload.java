package com.everyones.lawmaking.common.dto.response.election.feed;

import com.everyones.lawmaking.domain.entity.election.ElectionNews;
import com.fasterxml.jackson.annotation.JsonProperty;

public record NewsFeedPayload(
        @JsonProperty("news_id") Long newsId,
        @JsonProperty("title") String title,
        @JsonProperty("description") String description,
        @JsonProperty("link") String link,
        @JsonProperty("source") String source,
        @JsonProperty("thumbnail_url") String thumbnailUrl,
        @JsonProperty("matched_party") String matchedParty,
        @JsonProperty("matched_region") String matchedRegion
) {
    public static NewsFeedPayload from(ElectionNews news) {
        return new NewsFeedPayload(
                news.getId(),
                news.getTitle(),
                news.getDescription(),
                news.getLink(),
                news.getSource(),
                news.getThumbnailUrl(),
                news.getMatchedParty(),
                news.getMatchedRegion()
        );
    }
}
