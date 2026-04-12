package com.everyones.lawmaking.service.election.poll;

import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class PollNormalizationService {

    private static final Map<String, String> REGION_LABEL_BY_CODE = Map.of(
            "11", "서울특별시 전체",
            "41", "경기도 전체"
    );

    private static final Map<String, String> REGION_LABEL_BY_NAME = Map.of(
            "서울특별시", "서울특별시 전체",
            "경기도", "경기도 전체"
    );

    private static final Map<String, String> ELECTION_LABEL_BY_ID = Map.of(
            "local-2026", "제9회 전국동시지방선거",
            "20260603", "제9회 전국동시지방선거"
    );

    private static final List<String> CANONICAL_PARTY_NAMES = List.of(
            "더불어민주당",
            "국민의힘",
            "개혁신당",
            "조국혁신당",
            "진보당",
            "정의당",
            "기본소득당",
            "새로운미래",
            "자유통일당",
            "민주노동당",
            "노동당",
            "녹색당",
            "무소속"
    );

    private static final Map<String, String> CANDIDATE_ALIAS_MAP = Map.of(
            "김 동 연", "김동연"
    );

    public String normalizeRegionLabel(String regionCode, String regionName) {
        String normalizedCode = normalizeValue(regionCode);
        String normalizedName = normalizeValue(regionName);

        if (REGION_LABEL_BY_CODE.containsKey(normalizedCode)) {
            return REGION_LABEL_BY_CODE.get(normalizedCode);
        }

        if (REGION_LABEL_BY_NAME.containsKey(normalizedName)) {
            return REGION_LABEL_BY_NAME.get(normalizedName);
        }

        return normalizedName;
    }

    public String normalizeElectionLabel(String electionId) {
        return ELECTION_LABEL_BY_ID.getOrDefault(normalizeValue(electionId), normalizeValue(electionId));
    }

    public String normalizePartyName(String partyName) {
        String normalizedValue = normalizeValue(partyName);
        if (normalizedValue.isEmpty() || normalizedValue.equals("undecided")) {
            return normalizedValue;
        }

        String collapsedValue = collapseSpaces(normalizedValue);
        return CANONICAL_PARTY_NAMES.stream()
                .filter(canonicalName -> collapseSpaces(canonicalName).equals(collapsedValue))
                .findFirst()
                .orElse(normalizedValue);
    }

    public String normalizeCandidateName(String candidateName) {
        return CANDIDATE_ALIAS_MAP.getOrDefault(normalizeValue(candidateName), collapseSpaces(candidateName));
    }

    private String normalizeValue(String value) {
        return value == null ? "" : value.trim();
    }

    private String collapseSpaces(String value) {
        return value == null ? "" : value.replaceAll("\\s+", "");
    }
}
