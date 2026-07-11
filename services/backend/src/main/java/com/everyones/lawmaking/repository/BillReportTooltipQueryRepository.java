package com.everyones.lawmaking.repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class BillReportTooltipQueryRepository {
    private static final String CURRENT_RENDERED_SUMMARIES_SQL = """
            SELECT tooltip.bill_id, tooltip.rendered_summary
            FROM BillReportTooltip tooltip
            JOIN Bill bill ON bill.bill_id = tooltip.bill_id
            WHERE tooltip.bill_id IN (:billIds)
              AND tooltip.status = 'APPLIED'
              AND tooltip.rendered_summary IS NOT NULL
              AND tooltip.source_report_hash = SHA2(bill.gpt_summary, 256)
            """;

    private final NamedParameterJdbcTemplate jdbcTemplate;

    public Map<String, String> findCurrentRenderedSummaries(List<String> billIds) {
        if (billIds.isEmpty()) {
            return Map.of();
        }

        var parameters = new MapSqlParameterSource("billIds", billIds);
        return jdbcTemplate.query(CURRENT_RENDERED_SUMMARIES_SQL, parameters, resultSet -> {
            Map<String, String> summaries = new LinkedHashMap<>();
            while (resultSet.next()) {
                summaries.put(resultSet.getString("bill_id"), resultSet.getString("rendered_summary"));
            }
            return summaries;
        });
    }
}
