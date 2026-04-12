package com.everyones.lawmaking.common.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

public record BookmarkRequest(
        @NotBlank @JsonProperty("feed_type") String feedType,
        @NotBlank @JsonProperty("feed_item_id") String feedItemId
) {}
