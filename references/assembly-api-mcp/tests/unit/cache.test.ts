import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createCache, buildCacheKey, type Cache } from "../../src/api/cache.js";
import type { CacheConfig } from "../../src/config.js";

function createCacheConfig(overrides: Partial<CacheConfig> = {}): CacheConfig {
  return {
    enabled: true,
    ttlStatic: 86400,
    ttlDynamic: 3600,
    ...overrides,
  };
}

describe("createCache", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("get / set", () => {
    it("저장한 데이터를 조회한다", () => {
      const cache = createCache(createCacheConfig());
      cache.set("key1", { value: "hello" }, 60);

      const result = cache.get<{ value: string }>("key1");
      expect(result).toEqual({ value: "hello" });
    });

    it("존재하지 않는 키는 undefined를 반환한다", () => {
      const cache = createCache(createCacheConfig());

      expect(cache.get("nonexistent")).toBeUndefined();
    });

    it("캐시 히트/미스를 정확히 카운트한다", () => {
      const cache = createCache(createCacheConfig());
      cache.set("key1", "data", 60);

      cache.get("key1"); // hit
      cache.get("key1"); // hit
      cache.get("missing"); // miss

      const s = cache.stats();
      expect(s.hits).toBe(2);
      expect(s.misses).toBe(1);
      expect(s.size).toBe(1);
    });
  });

  describe("TTL 만료", () => {
    it("TTL이 지나면 캐시에서 제거된다", () => {
      const cache = createCache(createCacheConfig());
      cache.set("key1", "data", 10);

      // TTL 이전
      vi.advanceTimersByTime(9_000);
      expect(cache.get("key1")).toBe("data");

      // TTL 초과
      vi.advanceTimersByTime(2_000);
      expect(cache.get("key1")).toBeUndefined();
    });

    it("만료된 엔트리 접근은 미스로 카운트된다", () => {
      const cache = createCache(createCacheConfig());
      cache.set("key1", "data", 5);

      vi.advanceTimersByTime(6_000);
      cache.get("key1"); // expired → miss

      expect(cache.stats().misses).toBe(1);
      expect(cache.stats().hits).toBe(0);
    });

    it("서로 다른 TTL을 가진 엔트리가 독립적으로 만료된다", () => {
      const cache = createCache(createCacheConfig());
      cache.set("short", "a", 5);
      cache.set("long", "b", 60);

      vi.advanceTimersByTime(6_000);
      expect(cache.get("short")).toBeUndefined();
      expect(cache.get("long")).toBe("b");
    });
  });

  describe("invalidate", () => {
    it("특정 키를 삭제한다", () => {
      const cache = createCache(createCacheConfig());
      cache.set("key1", "data1", 60);
      cache.set("key2", "data2", 60);

      cache.invalidate("key1");

      expect(cache.get("key1")).toBeUndefined();
      expect(cache.get("key2")).toBe("data2");
      expect(cache.stats().size).toBe(1);
    });

    it("존재하지 않는 키를 삭제해도 에러가 발생하지 않는다", () => {
      const cache = createCache(createCacheConfig());
      expect(() => cache.invalidate("nonexistent")).not.toThrow();
    });
  });

  describe("clear", () => {
    it("모든 엔트리와 통계를 초기화한다", () => {
      const cache = createCache(createCacheConfig());
      cache.set("key1", "a", 60);
      cache.set("key2", "b", 60);
      cache.get("key1"); // hit

      cache.clear();

      expect(cache.stats()).toEqual({ size: 0, hits: 0, misses: 0 });
      expect(cache.get("key1")).toBeUndefined();
    });
  });

  describe("캐시 비활성화", () => {
    it("enabled=false이면 set해도 저장하지 않는다", () => {
      const cache = createCache(createCacheConfig({ enabled: false }));
      cache.set("key1", "data", 60);

      expect(cache.get("key1")).toBeUndefined();
      expect(cache.stats().size).toBe(0);
    });

    it("enabled=false이면 get은 항상 미스를 반환한다", () => {
      const cache = createCache(createCacheConfig({ enabled: false }));
      cache.get("anything");

      expect(cache.stats().misses).toBe(1);
      expect(cache.stats().hits).toBe(0);
    });
  });
});

describe("buildCacheKey", () => {
  it("apiCode와 정렬된 파라미터로 키를 생성한다", () => {
    const key = buildCacheKey("TEST_API", { pSize: 20, pIndex: 1, Type: "json" });
    // localeCompare sorts uppercase T after lowercase p
    expect(key).toBe("TEST_API:pIndex=1&pSize=20&Type=json");
  });

  it("KEY 파라미터를 제외한다", () => {
    const key = buildCacheKey("TEST_API", { KEY: "secret", pIndex: 1 } as Record<string, string | number>);
    expect(key).not.toContain("secret");
    expect(key).toBe("TEST_API:pIndex=1");
  });

  it("파라미터가 없으면 apiCode만 반환한다", () => {
    const key = buildCacheKey("TEST_API", {});
    expect(key).toBe("TEST_API:");
  });

  it("동일한 파라미터 순서와 관계없이 같은 키를 생성한다", () => {
    const key1 = buildCacheKey("API", { a: "1", b: "2", c: "3" });
    const key2 = buildCacheKey("API", { c: "3", a: "1", b: "2" });
    expect(key1).toBe(key2);
  });
});
