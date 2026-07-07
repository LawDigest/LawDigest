/**
 * 국회 좌석도 배치 순서(왼→오른쪽).
 *
 * 의석 1위 정당을 왼쪽 끝, 2위 정당을 오른쪽 끝에 두고, 그 아래 순위 정당들을
 * 가운데에 의석 많은 순으로 채운다. 좌석은 이 순서대로 왼쪽부터 색을 채운다.
 *
 * 단, 진보당은 브랜드 색이 국민의힘(2위)과 유사한 빨강 계열이라 2위 옆에 붙으면
 * 경계가 구분되지 않으므로, 가운데 그룹의 맨 앞(1위 옆)에 고정 배치한다.
 */
export function orderPartiesByBloc<T extends { congressman_count: number; party_name: string }>(parties: T[]): T[] {
  const sorted = [...parties].sort((a, b) => b.congressman_count - a.congressman_count);
  if (sorted.length <= 2) return sorted;

  const [first, second, ...rest] = sorted;
  const progressive = rest.filter((party) => party.party_name.trim() === '진보당');
  const others = rest.filter((party) => party.party_name.trim() !== '진보당');
  // 왼쪽: 1위 → 진보당(색상 충돌 회피) → 나머지(의석 많은 순) → 오른쪽: 2위
  return [first, ...progressive, ...others, second];
}
