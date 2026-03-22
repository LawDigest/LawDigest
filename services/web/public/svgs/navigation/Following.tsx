import { NavIconProps } from '@/types';

export default function IconFollowing({ isActive }: NavIconProps) {
  return (
    <svg width="30" height="31" viewBox="0 0 30 31" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M5.65 26.9483V3.65H24.35V26.9483L15.2907 22.4186L15 22.2733L14.7093 22.4186L5.65 26.9483Z"
        fill={isActive ? 'currentColor' : 'none'}
        fillOpacity={isActive ? 0.9 : 0}
        stroke="currentColor"
        strokeWidth="1.3"
      />
    </svg>
  );
}
