/**
 * 입법예고 도구
 *
 * - get_legislation_notices: 입법예고 조회
 */

import { z } from "zod";
import { type McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { type AppConfig } from "../config.js";
import { createApiClient } from "../api/client.js";
import { API_CODES } from "../api/codes.js";

export function registerLegislationTools(
  server: McpServer,
  config: AppConfig,
): void {
  const api = createApiClient(config);

  server.tool(
    "get_legislation_notices",
    "진행중인 입법예고를 조회합니다. 키워드, 기간으로 필터링할 수 있습니다.",
    {
      keyword: z.string().optional().describe("검색 키워드 (법안명 검색)"),
      date_from: z.string().optional().describe("시작일 (YYYY-MM-DD 형식)"),
      date_to: z.string().optional().describe("종료일 (YYYY-MM-DD 형식)"),
      page: z.number().optional().describe("페이지 번호 (기본: 1)"),
      page_size: z.number().optional().describe("페이지 크기 (기본: 20, 최대: 100)"),
    },
    async (params) => {
      try {
        const queryParams: Record<string, string | number> = {};
        if (params.keyword) queryParams.BILL_NAME = params.keyword;
        if (params.date_from) queryParams.START_DT = params.date_from;
        if (params.date_to) queryParams.END_DT = params.date_to;
        if (params.page) queryParams.pIndex = params.page;
        if (params.page_size) queryParams.pSize = Math.min(params.page_size, config.apiResponse.maxPageSize);

        const result = await api.fetchOpenAssembly(
          API_CODES.LEGISLATION_ACTIVE,
          queryParams,
        );

        const formatted = result.rows.map((row) => ({
          의안번호: row.BILL_NO,
          법안명: row.BILL_NAME,
          대수: row.AGE,
          제안자구분: row.PROPOSER_KIND_CD,
          제안자: row.PROPOSER,
          소관위원회: row.CURR_COMMITTEE,
          예고종료일: row.NOTI_ED_DT,
          링크: row.LINK_URL,
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
