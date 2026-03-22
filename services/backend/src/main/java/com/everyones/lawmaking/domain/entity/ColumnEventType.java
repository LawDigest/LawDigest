package com.everyones.lawmaking.domain.entity;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.Arrays;
import java.util.List;


@AllArgsConstructor
@Getter
public enum ColumnEventType {
    RP_INSERT("rp_insert",
            "RepresentativeProposer",
            null,
            EventType.INSERT,
            List.of("congressman_id","bill_id")),
    BILL_STAGE_UPDATE(
            "bill_stage_update",
            "Bill",
            "stage",
            EventType.UPDATE,
            List.of("bill_id")),

    BILL_RESULT_UPDATE(
            "bill_result_update",
            "Bill",
            "bill_result",
            EventType.UPDATE,
            List.of("bill_id")),
    CONGRESSMAN_PARTY_UPDATE(
            "congressman_party_update",
            "Congressman",
            "party_id",
            EventType.UPDATE,
            List.of("congressman_id"));

    public enum EventType {
        INSERT, UPDATE, DELETE
    }
    private final String eventName;
    private final String tableName;
    private final String columnName;
    private final EventType eventType;
    private final List<String> keyColumns;

    public static ColumnEventType from(String code) {
        return Arrays.stream(ColumnEventType.values())
                .filter(cet -> cet.getEventName().equals(code))
                .findAny()
                .orElseThrow();
    }

    public static ColumnEventType findByEventName(String eventName) {
        return Arrays.stream(ColumnEventType.values())
                .filter(cet -> cet.name().equals(eventName))
                .findAny()
                .orElseThrow();
    }


}