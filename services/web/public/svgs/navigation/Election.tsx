import { NavIconProps } from '@/types';

export default function IconElection({ isActive }: NavIconProps) {
  return (
    <svg width="30" height="31" viewBox="0 0 30 31" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 한국 투표 도장 마크: 원 + 세로선 + 우하향 대각선 */}
      {/* 외곽 원 */}
      <circle
        cx="15"
        cy="15.5"
        r="12"
        stroke="currentColor"
        strokeWidth="2.2"
        fill={isActive ? 'currentColor' : 'none'}
        fillOpacity={isActive ? 0.12 : 0}
      />
      {/* 세로선 (중앙, 원 내부 상단~하단) */}
      <line x1="15" y1="3.5" x2="15" y2="27.5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      {/* 우하향 대각선 (세로선 중간~우하단) */}
      <line x1="15" y1="15.5" x2="26.2" y2="26.2" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}
