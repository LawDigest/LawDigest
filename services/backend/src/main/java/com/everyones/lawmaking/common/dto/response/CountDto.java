package com.everyones.lawmaking.common.dto.response;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class CountDto {
    private Long count;
    public static CountDto from(Long count) {
        return CountDto.builder()
                .count(count)
                .build();
    }
}
