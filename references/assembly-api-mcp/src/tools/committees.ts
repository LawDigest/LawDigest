/**
 * 위원회 정보 도구
 *
 * - get_committees: 위원회 목록 조회 (상임위/특별위)
 */

import { z } from "zod";
import { type McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { type AppConfig } from "../config.js";
import { createApiClient } from "../api/client.js";
import { API_CODES } from "../api/codes.js";

export function registerCommitteeTools(
  server: McpServer,
  config: AppConfig,
): void {
  const api = createApiClient(config);

  server.tool(
    "get_committees",
    "국회 위원회 목록을 조회합니다. 상임위원회, 특별위원회 등을 대수와 위원회 유형으로 필터링할 수 있습니다.",
    {
      age: z.number().optional().describe("대수 (예: 22 = 제22대 국회)"),
      committee_type: z.string().optional().describe("위원회 유형 (예: 상임위원회, 특별위원회)"),
      page: z.number().optional().describe("페이지 번호 (기본: 1)"),
      page_size: z.number().optional().describe("페이지 크기 (기본: 20, 최대: 100)"),
    },
    async (params) => {
      try {
        const queryParams: Record<string, string | number> = {};
        if (params.committee_type) queryParams.CMT_DIV_NM = params.committee_type;
        if (params.page) queryParams.pIndex = params.page;
        if (params.page_size) queryParams.pSize = Math.min(params.page_size, config.apiResponse.maxPageSize);

        const result = await api.fetchOpenAssembly(
          API_CODES.COMMITTEE_INFO,
          queryParams,
        );

        const formatted = result.rows.map((row) => ({
          위원회구분: row.CMT_DIV_NM,
          위원회명: row.COMMITTEE_NAME,
          위원회코드: row.HR_DEPT_CD,
          위원장: row.HG_NM,
          간사: row.HG_NM_LIST,
          정원: row.LIMIT_CNT,
          현원: row.CURR_CNT,
        }));

        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify({ total: result.totalCount, items: formatted }),
          }],
        };
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        const code = message.includes('API_KEY') ? 'AUTH_ERROR'
          : message.includes('rate') ? 'RATE_LIMIT'
          : message.includes('timeout') ? 'TIMEOUT'
          : 'UNKNOWN';
        return {
          content: [{ type: "text" as const, text: JSON.stringify({ error: message, code }) }],
          isError: true,
        };
      }
    },
  );
}
