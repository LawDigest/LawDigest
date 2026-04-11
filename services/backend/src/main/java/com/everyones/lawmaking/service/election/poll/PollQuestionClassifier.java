package com.everyones.lawmaking.service.election.poll;

import org.springframework.stereotype.Component;

@Component
public class PollQuestionClassifier {

    public enum QuestionType {
        PARTY_SUPPORT,
        CANDIDATE_FIT,
        MATCHUP,
        OTHER
    }

    public QuestionType classify(String questionTitle, String questionText) {
        String title = normalize(questionTitle);
        String text = normalize(questionText);

        if (containsAny(title, text, "정당지지도", "지지정당")) {
            return QuestionType.PARTY_SUPPORT;
        }

        if (containsAny(title, text, "후보 적합도", "후보지지도", "후보 지지도", "누가 가장 적합")) {
            return QuestionType.CANDIDATE_FIT;
        }

        if (containsAny(title, text, "가상대결", "양자대결", "누구에게 투표", "맞붙는다면")) {
            return QuestionType.MATCHUP;
        }

        return QuestionType.OTHER;
    }

    private boolean containsAny(String title, String text, String... keywords) {
        for (String keyword : keywords) {
            String normalizedKeyword = normalize(keyword);
            if (title.contains(normalizedKeyword) || text.contains(normalizedKeyword)) {
                return true;
            }
        }
        return false;
    }

    private String normalize(String value) {
        if (value == null) {
            return "";
        }
        return value.replaceAll("\\s+", "").trim();
    }
}
