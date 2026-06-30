import { NavIconProps } from '@/types';

export default function IconExplore({ isActive }: NavIconProps) {
  return (
    <svg width="30" height="31" viewBox="0 0 30 31" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 탐색(나침반) 마크: 원 + 다이아몬드 바늘 */}
      <circle
        cx="15"
        cy="15.5"
        r="12"
        stroke="currentColor"
        strokeWidth="2"
        fill={isActive ? 'currentColor' : 'none'}
        fillOpacity={isActive ? 0.12 : 0}
      />
      {/* 나침반 바늘 (우상→좌하 채워진 마름모) */}
      <path
        d="M19.6 10.9 L16.1 16.6 L10.4 20.1 L13.9 14.4 Z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}
