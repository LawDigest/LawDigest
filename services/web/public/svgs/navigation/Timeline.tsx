import { NavIconProps } from '@/types';

export default function IconTimeline({ isActive }: NavIconProps) {
  return (
    <svg width="30" height="31" viewBox="0 0 30 31" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 활성 시: 달력 본체 채우기 */}
      {isActive && (
        <path
          d="M3.75 8.9144C3.75 7.4377 4.89473 6.2406 6.30682 6.2406H23.7953C25.1509 6.2406 26.2498 7.4377 26.2498 8.9144V24.8692C26.2498 26.2099 25.1307 27.2967 23.75 27.2967H6.25C4.86929 27.2967 3.75 26.2099 3.75 24.8692V8.9144Z"
          fill="currentColor"
          fillOpacity={0.15}
        />
      )}
      <path
        d="M18.75 6.66276V4.23523M18.75 6.66276V9.09028M18.75 6.66276H13.125M3.75 13.9453V24.8692C3.75 26.2099 4.86929 27.2967 6.25 27.2967H23.75C25.1307 27.2967 26.25 26.2099 26.25 24.8692V13.9453H3.75Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M3.75 14.262V8.9144C3.75 7.4377 4.89473 6.2406 6.30682 6.2406H8.86364"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8.86328 4.23523V9.2486"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M26.2498 14.262V8.9144C26.2498 7.4377 25.1509 6.2406 23.7953 6.2406H23.1816"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
