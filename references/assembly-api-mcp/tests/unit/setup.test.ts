/**
 * setup.ts 단위 테스트
 *
 * 대화형 입력이 필요한 runSetup()은 통합 테스트로 별도 검증.
 * 여기서는 index.ts의 setup 분기와 setup 모듈 로딩을 검증합니다.
 */

import { describe, it, expect } from "vitest";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

describe("setup 모듈", () => {
  it("dist/setup.js 빌드 파일이 존재한다", () => {
    const setupPath = resolve(process.cwd(), "dist/setup.js");
    expect(existsSync(setupPath)).toBe(true);
  });

  it("setup 모듈을 dynamic import할 수 있다", async () => {
    const mod = await import("../../src/setup.js");
    expect(typeof mod.runSetup).toBe("function");
  });

  it("index.ts에서 setup 명령 분기가 존재한다", async () => {
    const indexSource = await import("node:fs/promises").then((fs) =>
      fs.readFile(resolve(process.cwd(), "src/index.ts"), "utf-8"),
    );
    expect(indexSource).toContain('command === "setup"');
    expect(indexSource).toContain('./setup.js');
  });
});
