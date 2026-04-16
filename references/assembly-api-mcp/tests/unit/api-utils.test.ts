import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  createMonitor,
  type Monitor,
  type ApiCallMetric,
} from "../../src/api/monitor.js";
import {
  createRateLimiter,
  type RateLimiter,
} from "../../src/api/rate-limiter.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeMetric(
  overrides: Partial<ApiCallMetric> = {},
): ApiCallMetric {
  return {
    apiCode: "TEST_API",
    durationMs: 100,
    timestamp: Date.now(),
    success: true,
    ...overrides,
  };
}

// ===========================================================================
// Monitor
// ===========================================================================

describe("createMonitor", () => {
  let stderrSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    stderrSpy = vi.spyOn(process.stderr, "write").mockReturnValue(true);
  });

  afterEach(() => {
    stderrSpy.mockRestore();
  });

  // -----------------------------------------------------------------------
  // stats
  // -----------------------------------------------------------------------

  describe("stats", () => {
    it("빈 상태에서 모든 값이 0이다", () => {
      const monitor = createMonitor();
      const s = monitor.stats();

      expect(s).toEqual({
        totalCalls: 0,
        successCount: 0,
        failureCount: 0,
        avgDurationMs: 0,
        slowCallCount: 0,
      });
    });

    it("성공 호출을 기록하면 totalCalls=1, successCount=1", () => {
      const monitor = createMonitor();
      monitor.record(makeMetric({ success: true }));
      const s = monitor.stats();

      expect(s.totalCalls).toBe(1);
      expect(s.successCount).toBe(1);
      expect(s.failureCount).toBe(0);
    });

    it("실패 호출을 기록하면 failureCount=1", () => {
      const monitor = createMonitor();
      monitor.record(makeMetric({ success: false }));
      const s = monitor.stats();

      expect(s.totalCalls).toBe(1);
      expect(s.successCount).toBe(0);
      expect(s.failureCount).toBe(1);
    });

    it("여러 호출의 평균 지속 시간을 올바르게 계산한다", () => {
      const monitor = createMonitor();
      monitor.record(makeMetric({ durationMs: 100 }));
      monitor.record(makeMetric({ durationMs: 200 }));
      monitor.record(makeMetric({ durationMs: 300 }));
      const s = monitor.stats();

      expect(s.totalCalls).toBe(3);
      expect(s.avgDurationMs).toBe(200);
    });

    it("성공·실패 혼합 호출의 통계가 정확하다", () => {
      const monitor = createMonitor();
      monitor.record(makeMetric({ success: true, durationMs: 100 }));
      monitor.record(makeMetric({ success: false, durationMs: 200 }));
      monitor.record(makeMetric({ success: true, durationMs: 300 }));
      const s = monitor.stats();

      expect(s.totalCalls).toBe(3);
      expect(s.successCount).toBe(2);
      expect(s.failureCount).toBe(1);
      expect(s.avgDurationMs).toBe(200);
    });
  });

  // -----------------------------------------------------------------------
  // slowCalls
  // -----------------------------------------------------------------------

  describe("slowCalls", () => {
    it("3000ms 이하 호출은 느린 호출 목록에 포함되지 않는다", () => {
      const monitor = createMonitor();
      monitor.record(makeMetric({ durationMs: 2999 }));
      monitor.record(makeMetric({ durationMs: 3000 }));

      expect(monitor.slowCalls()).toHaveLength(0);
      expect(monitor.stats().slowCallCount).toBe(0);
      expect(stderrSpy).not.toHaveBeenCalled();
    });

    it("3000ms 초과 호출은 느린 호출 목록에 포함되고 stderr 경고를 출력한다", () => {
      const monitor = createMonitor();
      const slowMetric = makeMetric({ durationMs: 3001, apiCode: "SLOW_API" });
      monitor.record(slowMetric);

      const slow = monitor.slowCalls();
      expect(slow).toHaveLength(1);
      expect(slow[0]).toEqual(slowMetric);
      expect(monitor.stats().slowCallCount).toBe(1);
      expect(stderrSpy).toHaveBeenCalledWith(
        expect.stringContaining("SLOW_API"),
      );
      expect(stderrSpy).toHaveBeenCalledWith(
        expect.stringContaining("3001"),
      );
    });

    it("최대 100개의 느린 호출만 저장하고 가장 오래된 것부터 제거한다", () => {
      const monitor = createMonitor();

      // 101개의 느린 호출 기록
      for (let i = 0; i < 101; i++) {
        monitor.record(
          makeMetric({
            durationMs: 5000,
            apiCode: `API_${String(i)}`,
            timestamp: i,
          }),
        );
      }

      const slow = monitor.slowCalls();
      expect(slow).toHaveLength(100);
      // 첫 번째(API_0)는 제거되고, API_1부터 API_100까지 남아야 함
      expect(slow[0]?.apiCode).toBe("API_1");
      expect(slow[99]?.apiCode).toBe("API_100");
      expect(monitor.stats().slowCallCount).toBe(100);
    });
  });
});

// ===========================================================================
// RateLimiter
// ===========================================================================

describe("createRateLimiter", () => {
  let stderrSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    stderrSpy = vi.spyOn(process.stderr, "write").mockReturnValue(true);
  });

  afterEach(() => {
    stderrSpy.mockRestore();
  });

  // -----------------------------------------------------------------------
  // initial state
  // -----------------------------------------------------------------------

  describe("초기 상태", () => {
    it("count=0, remaining=10000", () => {
      const limiter = createRateLimiter();

      expect(limiter.remaining()).toBe(10_000);
      expect(limiter.isNearLimit()).toBe(false);
    });

    it("state()가 전체 상태 객체를 반환한다", () => {
      const limiter = createRateLimiter();
      const s = limiter.state();

      expect(s.count).toBe(0);
      expect(s.monthlyLimit).toBe(10_000);
      expect(s.remaining).toBe(10_000);
      expect(s.isNearLimit).toBe(false);
      expect(s.resetMonth).toMatch(/^\d{4}-\d{2}$/);
    });
  });

  // -----------------------------------------------------------------------
  // increment / remaining
  // -----------------------------------------------------------------------

  describe("increment", () => {
    it("호출하면 count가 증가한다", () => {
      const limiter = createRateLimiter();
      limiter.increment();

      expect(limiter.state().count).toBe(1);
    });

    it("increment 후 remaining이 감소한다", () => {
      const limiter = createRateLimiter();
      limiter.increment();

      expect(limiter.remaining()).toBe(9_999);
    });
  });

  // -----------------------------------------------------------------------
  // isNearLimit / threshold warnings
  // -----------------------------------------------------------------------

  describe("임계값 경고", () => {
    it("80% 미만이면 isNearLimit=false", () => {
      const limiter = createRateLimiter(100);

      for (let i = 0; i < 79; i++) {
        limiter.increment();
      }

      expect(limiter.isNearLimit()).toBe(false);
    });

    it("80% 도달 시 isNearLimit=true이고 stderr 경고를 출력한다", () => {
      const limiter = createRateLimiter(100);

      for (let i = 0; i < 80; i++) {
        limiter.increment();
      }

      expect(limiter.isNearLimit()).toBe(true);
      expect(stderrSpy).toHaveBeenCalledWith(
        expect.stringContaining("80%"),
      );
    });

    it("80% 경고는 한 번만 출력된다", () => {
      const limiter = createRateLimiter(100);

      for (let i = 0; i < 85; i++) {
        limiter.increment();
      }

      const warnCalls = stderrSpy.mock.calls.filter((call) =>
        String(call[0]).includes("80%"),
      );
      expect(warnCalls).toHaveLength(1);
    });

    it("100% 도달 시 매번 stderr 경고를 출력한다", () => {
      const limiter = createRateLimiter(100);

      for (let i = 0; i < 103; i++) {
        limiter.increment();
      }

      // 100, 101, 102, 103 → 한도 도달 경고 4번
      const limitCalls = stderrSpy.mock.calls.filter((call) =>
        String(call[0]).includes("한도 도달"),
      );
      expect(limitCalls).toHaveLength(4);
    });

    it("100% 도달 시 remaining은 0이다", () => {
      const limiter = createRateLimiter(100);

      for (let i = 0; i < 105; i++) {
        limiter.increment();
      }

      expect(limiter.remaining()).toBe(0);
    });
  });

  // -----------------------------------------------------------------------
  // reset
  // -----------------------------------------------------------------------

  describe("reset", () => {
    it("count를 0으로 되돌린다", () => {
      const limiter = createRateLimiter(100);

      for (let i = 0; i < 50; i++) {
        limiter.increment();
      }

      limiter.reset();

      expect(limiter.state().count).toBe(0);
      expect(limiter.remaining()).toBe(100);
      expect(limiter.isNearLimit()).toBe(false);
    });

    it("reset 후 80% 경고가 다시 발생한다", () => {
      const limiter = createRateLimiter(100);

      // 첫 번째 80% 도달
      for (let i = 0; i < 80; i++) {
        limiter.increment();
      }

      limiter.reset();
      stderrSpy.mockClear();

      // 두 번째 80% 도달
      for (let i = 0; i < 80; i++) {
        limiter.increment();
      }

      expect(stderrSpy).toHaveBeenCalledWith(
        expect.stringContaining("80%"),
      );
    });
  });

  // -----------------------------------------------------------------------
  // custom monthly limit
  // -----------------------------------------------------------------------

  describe("커스텀 월간 한도", () => {
    it("사용자 지정 한도를 적용한다", () => {
      const limiter = createRateLimiter(500);
      const s = limiter.state();

      expect(s.monthlyLimit).toBe(500);
      expect(s.remaining).toBe(500);
    });
  });
});
