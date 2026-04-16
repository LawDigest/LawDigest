import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { loadConfig, API_BASE_URLS, ASSEMBLY_ERROR_CODES } from "../../src/config.js";

describe("config", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    // 테스트마다 환경 변수 초기화
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe("loadConfig", () => {
    it("ASSEMBLY_API_KEY가 없으면 에러를 던진다", () => {
      delete process.env.ASSEMBLY_API_KEY;
      expect(() => loadConfig()).toThrow("ASSEMBLY_API_KEY");
    });

    it("ASSEMBLY_API_KEY가 있으면 설정을 반환한다", () => {
      process.env.ASSEMBLY_API_KEY = "test-key";
      const config = loadConfig();
      expect(config.apiKeys.assemblyApiKey).toBe("test-key");
    });

    it("선택 키가 없으면 undefined를 반환한다", () => {
      process.env.ASSEMBLY_API_KEY = "test-key";
      delete process.env.DATA_GO_KR_SERVICE_KEY;
      delete process.env.NANET_API_KEY;
      delete process.env.NABO_API_KEY;
      const config = loadConfig();
      expect(config.apiKeys.dataGoKrServiceKey).toBeUndefined();
      expect(config.apiKeys.nanetApiKey).toBeUndefined();
      expect(config.apiKeys.naboApiKey).toBeUndefined();
    });

    it("서버 기본값이 올바르다", () => {
      process.env.ASSEMBLY_API_KEY = "test-key";
      const config = loadConfig();
      expect(config.server.transport).toBe("stdio");
      expect(config.server.port).toBe(3000);
      expect(config.server.logLevel).toBe("info");
    });

    it("캐시 기본값이 올바르다", () => {
      process.env.ASSEMBLY_API_KEY = "test-key";
      const config = loadConfig();
      expect(config.cache.enabled).toBe(true);
      expect(config.cache.ttlStatic).toBe(86400);
      expect(config.cache.ttlDynamic).toBe(3600);
    });

    it("환경 변수로 설정을 오버라이드할 수 있다", () => {
      process.env.ASSEMBLY_API_KEY = "test-key";
      process.env.MCP_TRANSPORT = "http";
      process.env.MCP_PORT = "8080";
      process.env.CACHE_ENABLED = "false";
      const config = loadConfig();
      expect(config.server.transport).toBe("http");
      expect(config.server.port).toBe(8080);
      expect(config.cache.enabled).toBe(false);
    });

    it("잘못된 정수값은 에러를 던진다", () => {
      process.env.ASSEMBLY_API_KEY = "test-key";
      process.env.MCP_PORT = "not-a-number";
      expect(() => loadConfig()).toThrow("유효한 정수");
    });
  });

  describe("API_BASE_URLS", () => {
    it("올바른 Base URL을 포함한다", () => {
      expect(API_BASE_URLS.openAssembly).toContain("open.assembly.go.kr");
      expect(API_BASE_URLS.dataGoKr).toContain("apis.data.go.kr");
    });
  });

  describe("ASSEMBLY_ERROR_CODES", () => {
    it("주요 에러코드가 정의되어 있다", () => {
      expect(ASSEMBLY_ERROR_CODES["INFO-000"]).toBeDefined();
      expect(ASSEMBLY_ERROR_CODES["INFO-200"]).toContain("인증키");
      expect(ASSEMBLY_ERROR_CODES["INFO-300"]).toContain("제한");
    });
  });
});
