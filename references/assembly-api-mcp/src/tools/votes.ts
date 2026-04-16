/**
 * 표결 정보 도구
 *
 * - get_vote_results: 의안별 표결 결과 조회
 */

import { z } from "zod";
import { type McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { type AppConfig } from "../config.js";
import { createApiClient } from "../api/client.js";
import { API_CODES, CURRENT_AGE } from "../api/codes.js";

export function registerVoteTools(
  server: McpServer,
  config: AppConfig,
): void {
  const api = createApiClient(config);

  server.tool(
    "get_vote_results",
    "의안별 표결 결과를 조회합니다. 의안 ID로 검색하여 각 의원의 찬성/반대/기권 정보를 반환합니다.",
    {
      bill_id: z.string().describe("의안 ID (필수)"),
      age: z.number().optional().describe("대수 (예: 22 = 제22대 국회)"),
      page: z.number().optional().describe("페이지 번호 (기본: 1)"),
      page_size: z.number().optional().describe("페이지 크기 (기본: 20, 최대: 100)"),
    },
    async (params) => {
      try {
        const queryParams: Record<string, string | number> = {
          BILL_ID: params.bill_id,
          AGE: params.age ?? CURRENT_AGE,
        };
        if (params.page) queryParams.pIndex = params.page;
        if (params.page_size) queryParams.pSize = Math.min(params.page_size, config.apiResponse.maxPageSize);

        const result = await api.fetchOpenAssembly(
          API_CODES.VOTE_BY_BILL,
          queryParams,
        );

        const formatted = result.rows.map((row) => ({
          의안ID: row.BILL_ID,
          의안명: row.BILL_NAME,
          의원명: row.HG_NM,
          표결결과: row.VOTE_RESULT,
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
