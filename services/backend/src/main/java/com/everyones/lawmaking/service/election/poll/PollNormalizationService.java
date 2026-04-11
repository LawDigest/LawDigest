package com.everyones.lawmaking.service.election.poll;

import org.springframework.stereotype.Service;

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
            "local-2026", "제9회 전국동시지방선거"
    );

    private static final Map<String, String> PARTY_ALIAS_MAP = Map.of(
            "더불어 민주당", "더불어민주당"
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
        return PARTY_ALIAS_MAP.getOrDefault(normalizeValue(partyName), normalizeValue(partyName));
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
