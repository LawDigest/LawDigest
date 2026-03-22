package com.everyones.lawmaking.global.constant;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.Getter;
import lombok.AllArgsConstructor;

public class BillStageType {
    // 상수 정의
    public static final BillStageType WITHDRAWAL = new BillStageType(0, "철회", "철회");
    public static final BillStageType RECEIPT = new BillStageType(1, "접수", "접수");
    public static final BillStageType STANDING_COMMITTEE_RECEIPT = new BillStageType(2, "위원회 심사", "소관위접수");
    public static final BillStageType STANDING_COMMITTEE_AUDIT_BEFORE = new BillStageType(3, "위원회 심사", "위원회 심사");
    public static final BillStageType SYSTEMATIC_REVIEW = new BillStageType(4, "체계자구 심사", "체계자구 심사");
    public static final BillStageType PLENARY_SESSION = new BillStageType(5, "본회의 심의", "본회의 심의");
    public static final BillStageType GOVERNMENT_TRANSFER = new BillStageType(6, "정부이송", "정부이송");
    public static final BillStageType PROMULGATION = new BillStageType(7, "공포", "공포");

    private static final Map<String, List<String>> KEY_MAP = new HashMap<>();
    private static final List<BillStageType> PREDEFINED_STAGES = new ArrayList<>();
    private static final Map<String, BillStageType> VALUE_MAP = new HashMap<>();

    static {
        PREDEFINED_STAGES.add(WITHDRAWAL);
        PREDEFINED_STAGES.add(RECEIPT);
        PREDEFINED_STAGES.add(STANDING_COMMITTEE_RECEIPT);
        PREDEFINED_STAGES.add(STANDING_COMMITTEE_AUDIT_BEFORE);
        PREDEFINED_STAGES.add(SYSTEMATIC_REVIEW);
        PREDEFINED_STAGES.add(PLENARY_SESSION);
        PREDEFINED_STAGES.add(GOVERNMENT_TRANSFER);
        PREDEFINED_STAGES.add(PROMULGATION);

        for (BillStageType stage : PREDEFINED_STAGES) {
            KEY_MAP.computeIfAbsent(stage.getKey(), k -> new ArrayList<>()).add(stage.getValue());
            VALUE_MAP.put(stage.getValue(), stage);
        }
    }

    @Getter
    private final int order;

    @Getter
    private final String key;

    @Getter
    private final String value;

    @Getter
    private final boolean predefined;

    // 사전 정의된 단계 생성자
    private BillStageType(int order, String key, String value) {
        this.order = order;
        this.key = key;
        this.value = value;
        this.predefined = true;
    }

    // 사전 정의되지 않은 단계 생성자
    private BillStageType(String key, String value) {
        this.order = -1; // 사전 정의되지 않은 단계는 순서를 -1로 표시
        this.key = key;
        this.value = value;
        this.predefined = false;
    }

    /**
     * 현재 단계에서 다음 단계로 업데이트 가능한지 확인
     * 1. 사전 정의된 단계 간 이동: 순서가 증가하는 방향으로만 가능
     * 2. 사전 정의되지 않은 단계로 이동: 항상 가능
     */
    public static boolean canUpdateStage(BillStageType current, BillStageType next) {
        // 대상 단계가 사전 정의되지 않은 경우 항상 업데이트 가능
        if (!next.isPredefined()) {
            return true;
        }

        // 현재 단계가 사전 정의되지 않은 경우, 사전 정의된 단계로 항상 업데이트 가능
        if (!current.isPredefined()) {
            return true;
        }

        // 둘 다 사전 정의된 단계인 경우, 순서가 증가해야만 업데이트 가능
        return current.getOrder() < next.getOrder();
    }

    /**
     * value로 BillStageType 찾기
     * 사전 정의된 단계에 없으면 새로운 BillStageType 생성
     */
    public static BillStageType fromValue(String value) {
        BillStageType stage = VALUE_MAP.get(value);
        if (stage != null) {
            return stage;
        }

        // 사전 정의된 단계에 없는 경우 새로운 단계 생성
        // 여기서는 key와 value를 동일하게 설정
        return new BillStageType(value, value);
    }

    /**
     * 지정된 key에 해당하는 단계가 존재하는지 확인
     */
    public static boolean containsValue(String stage) {
        return KEY_MAP.containsKey(stage);
    }
    

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;

        BillStageType that = (BillStageType) obj;
        return value.equals(that.value);
    }

    @Override
    public int hashCode() {
        return value.hashCode();
    }

    @Override
    public String toString() {
        return "BillStageType{" +
                "order=" + order +
                ", key='" + key + '\'' +
                ", value='" + value + '\'' +
                ", predefined=" + predefined +
                '}';
    }
}