import { NavIconProps } from '@/types';

export default function IconElection({ isActive }: NavIconProps) {
  return (
    <svg width="30" height="31" viewBox="0 0 30 31" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 활성 시: 투표함 채우기 */}
      {isActive && (
        <rect
          x="4.5"
          y="13.5"
          width="21"
          height="13"
          rx="1.5"
          fill="currentColor"
          fillOpacity={0.15}
        />
      )}
      {/* 투표함 몸체 */}
      <rect
        x="4.5"
        y="13.5"
        width="21"
        height="13"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      {/* 투표 용지 투입구 */}
      <path
        d="M10.5 13.5V11.5C10.5 10.948 10.948 10.5 11.5 10.5H18.5C19.052 10.5 19.5 10.948 19.5 11.5V13.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* 투입구 슬롯 */}
      <path
        d="M12 17.5H18"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      {/* 체크 표시 */}
      <path
        d="M11.5 21L13.5 23L18.5 19"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* 상단 국회 / 별 */}
      <path
        d="M15 4.5L15.9 7.3H18.9L16.5 9L17.4 11.8L15 10.1L12.6 11.8L13.5 9L11.1 7.3H14.1L15 4.5Z"
        fill={isActive ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
    </svg>
  );
}
