/**
 * 국회 본회의장 좌석을 형상화한 반원형(hemicycle) 좌석 배치 계산.
 *
 * 전체 좌석을 여러 개의 동심 반원(행)에 나눠 배치한다. 각 행의 좌석 수는
 * 반지름에 비례하도록 배분하여 좌석 밀도를 고르게 유지하고, 좌석을 각도 순으로
 * 정렬해 반환한다. 정렬된 순서대로 정당 색을 채우면 각 정당이 연속된 부채꼴(wedge)을
 * 차지하는, 흔히 보는 의석 분포 다이어그램이 된다.
 */

export interface HemicycleSeat {
  /** 반원 중심 기준 각도(라디안). PI=왼쪽 끝, 0=오른쪽 끝. */
  theta: number;
  /** 정규화 반지름(0~1). 1이 가장 바깥 행. */
  radius: number;
  /** 행 인덱스(0=가장 안쪽). */
  row: number;
}

export interface Hemicycle {
  rows: number;
  seats: HemicycleSeat[];
  /** 인접 행 간격(정규화). 좌석 반지름 산정에 사용. */
  rowGap: number;
}

/** 안쪽 행 반지름 / 바깥 행 반지름 비율. */
const INNER_RATIO = 0.42;

/**
 * 좌석 수에 맞는 행 개수를 추정한다. 반지름 방향 간격과 원주 방향 간격이
 * 비슷해지도록 rows ≈ sqrt(total·(1-inner) / (π·평균반지름))로 계산한다.
 */
function estimateRows(total: number): number {
  const avgRadius = (1 + INNER_RATIO) / 2;
  const estimate = Math.sqrt((total * (1 - INNER_RATIO)) / (Math.PI * avgRadius));
  return Math.max(2, Math.min(total, Math.round(estimate)));
}

export function buildHemicycle(total: number): Hemicycle {
  if (total <= 0) {
    return { rows: 0, seats: [], rowGap: 0 };
  }

  const rows = estimateRows(total);
  const radii = Array.from({ length: rows }, (_, i) => INNER_RATIO + ((1 - INNER_RATIO) * i) / (rows - 1));
  const radiusSum = radii.reduce((sum, r) => sum + r, 0);

  // 행별 좌석 수를 반지름에 비례 배분하고, 반올림 오차를 잔여분 큰 순서로 보정해 합계를 맞춘다.
  const rawCounts = radii.map((r) => (total * r) / radiusSum);
  const seatsPerRow = rawCounts.map((v) => Math.round(v));
  let remainder = total - seatsPerRow.reduce((sum, v) => sum + v, 0);
  const byFraction = rawCounts.map((v, i) => ({ i, frac: v - Math.floor(v) })).sort((a, b) => b.frac - a.frac);
  let cursor = 0;
  while (remainder !== 0) {
    const idx = byFraction[cursor % rows].i;
    if (remainder > 0) {
      seatsPerRow[idx] += 1;
      remainder -= 1;
    } else if (seatsPerRow[idx] > 0) {
      seatsPerRow[idx] -= 1;
      remainder += 1;
    }
    cursor += 1;
  }

  const seats: HemicycleSeat[] = [];
  for (let row = 0; row < rows; row += 1) {
    const count = seatsPerRow[row];
    const radius = radii[row];
    for (let j = 0; j < count; j += 1) {
      // 왼쪽(π) → 오른쪽(0)으로 좌석을 펼친다.
      const theta = count === 1 ? Math.PI / 2 : Math.PI * (1 - j / (count - 1));
      seats.push({ theta, radius, row });
    }
  }

  // 각도(왼→오) 순으로 정렬, 같은 각도면 안쪽 행부터. 정렬 순서대로 정당 색을 채운다.
  seats.sort((a, b) => b.theta - a.theta || a.radius - b.radius);

  const rowGap = (1 - INNER_RATIO) / (rows - 1);
  return { rows, seats, rowGap };
}
