package com.everyones.lawmaking.service.election.poll;

import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

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

    private static final Map<String, String> PARTY_ALIAS_MAP = Map.ofEntries(
            Map.entry("더불어민주당", "더불어민주당"),
            Map.entry("더불어민주", "더불어민주당"),
            Map.entry("더불어 민주당", "더불어민주당"),
            Map.entry("국민의힘", "국민의힘"),
            Map.entry("국민의 힘", "국민의힘"),
            Map.entry("개혁신당", "개혁신당"),
            Map.entry("개혁 신당", "개혁신당"),
            Map.entry("개혁신 당", "개혁신당"),
            Map.entry("조국혁신당", "조국혁신당"),
            Map.entry("조국 혁신당", "조국혁신당"),
            Map.entry("조국혁 신당", "조국혁신당"),
            Map.entry("진보당", "진보당")
    );

    private static final Map<String, String> CANDIDATE_ALIAS_MAP = Map.ofEntries(
            Map.entry("김 동 연", "김동연"),
            Map.entry("잘 모르겠다", "undecided"),
            Map.entry("잘모르겠다", "undecided"),
            Map.entry("모름/ 무응답", "undecided"),
            Map.entry("모름/무응답", "undecided"),
            Map.entry("없다", "undecided"),
            Map.entry("없음", "undecided")
    );

    private static final Pattern QUESTION_PLACEHOLDER_RE = Pattern.compile("^Q\\d+$", Pattern.CASE_INSENSITIVE);
    private static final Pattern OPTION_PLACEHOLDER_RE = Pattern.compile("^선택지\\d+$");
    private static final Pattern CORRUPTED_TEXT_RE = Pattern.compile("[\\u4e00-\\u9fff]");
    private static final Set<String> GENERIC_OPTION_NAMES = Set.of("정당", "후보", "인물");
    private static final List<String> PARTY_KEYWORDS = List.of(
            "더불어민주",
            "국민의힘",
            "조국혁신",
            "개혁신당",
            "진보당",
            "기본소득당",
            "사회민주당"
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
        String normalized = normalizeValue(partyName);
        String collapsed = collapseSpaces(partyName);
        return PARTY_ALIAS_MAP.getOrDefault(normalized, PARTY_ALIAS_MAP.getOrDefault(collapsed, normalized));
    }

    public String normalizeCandidateName(String candidateName) {
        String normalized = normalizeValue(candidateName);
        String collapsed = collapseSpaces(candidateName);
        return CANDIDATE_ALIAS_MAP.getOrDefault(normalized, CANDIDATE_ALIAS_MAP.getOrDefault(collapsed, collapsed));
    }

    public boolean isMeaningfulQuestionTitle(String questionTitle) {
        String normalized = normalizeValue(questionTitle);
        return !normalized.isEmpty()
                && !QUESTION_PLACEHOLDER_RE.matcher(normalized).matches()
                && !looksCorruptedText(normalized);
    }

    public boolean isSuspiciousPartyOption(String optionName) {
        String normalized = normalizeValue(optionName);
        String collapsed = collapseSpaces(optionName);

        if (normalized.isEmpty()
                || OPTION_PLACEHOLDER_RE.matcher(normalized).matches()
                || looksCorruptedText(normalized)
                || GENERIC_OPTION_NAMES.contains(normalized)) {
            return true;
        }

        long partyMatchCount = PARTY_KEYWORDS.stream()
                .filter(collapsed::contains)
                .count();
        if (partyMatchCount >= 2) {
            return true;
        }

        return collapsed.contains("더불어조국잘")
                || collapsed.contains("기타지지하는")
                || collapsed.contains("민주당국민의힘")
                || collapsed.contains("민주당혁신당모르겠다")
                || collapsed.contains("없음잘모름");
    }

    public boolean isSuspiciousCandidateOption(String optionName) {
        String normalized = normalizeValue(optionName);
        return normalized.isEmpty()
                || OPTION_PLACEHOLDER_RE.matcher(normalized).matches()
                || looksCorruptedText(normalized)
                || GENERIC_OPTION_NAMES.contains(normalized);
    }

    public boolean looksCorruptedText(String text) {
        return CORRUPTED_TEXT_RE.matcher(normalizeValue(text)).find();
    }

    private String normalizeValue(String value) {
        return value == null ? "" : value.trim();
    }

    private String collapseSpaces(String value) {
        return value == null ? "" : value.replaceAll("\\s+", "");
    }
}
