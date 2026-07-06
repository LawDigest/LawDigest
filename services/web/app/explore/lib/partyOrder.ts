/**
 * 국회 좌석도 배치를 위한 정당 정치 성향 순서(왼쪽=진보 → 오른쪽=보수).
 *
 * 조국혁신당을 비롯한 진보 소수정당을 최좌측에, 국민의힘을 최우측에 둔다.
 * 목록에 없는 정당(무소속 등)은 중앙에 배치한다.
 */
const PARTY_SPECTRUM_ORDER: string[] = [
  '진보당',
  '기본소득당',
  '사회민주당',
  '정의당',
  '녹색정의당',
  '조국혁신당',
  '더불어민주연합',
  '더불어민주당',
  '새로운미래',
  '개혁신당',
  '자유통일당',
  '국민의미래',
  '국민의힘',
];

/** 목록에 없는 정당을 중앙에 배치하기 위한 기준 순위. */
const CENTER_RANK = PARTY_SPECTRUM_ORDER.indexOf('더불어민주당') + 0.5;

/**
 * 정당명을 정치 성향 순위로 변환한다. getPartyColor와 동일하게 부분 일치로 매칭한다.
 * 낮을수록 왼쪽(진보), 높을수록 오른쪽(보수). 매칭 실패 시 중앙 순위를 반환한다.
 */
export function getPartySpectrumRank(partyName: string | null | undefined): number {
  if (!partyName) return CENTER_RANK;
  const trimmed = partyName.trim();
  if (!trimmed) return CENTER_RANK;

  const index = PARTY_SPECTRUM_ORDER.findIndex((name) => trimmed.includes(name) || name.includes(trimmed));
  return index === -1 ? CENTER_RANK : index;
}
