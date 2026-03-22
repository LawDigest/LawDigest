'use client';

import { useTheme } from 'next-themes';

export default function IconClock() {
  const { theme } = useTheme();

  return theme === 'dark' ? (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="9" cy="9" r="7" stroke="#999999" />
      <circle cx="9" cy="9" r="7" stroke="black" strokeOpacity="0.2" />
      <path d="M9 4.5V9H13.5" stroke="#999999" />
      <path d="M9 4.5V9H13.5" stroke="black" strokeOpacity="0.2" />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="18" height="18" fill="white" />
      <circle cx="9" cy="9" r="7" stroke="#999999" />
      <path d="M9 4.5V9H13.5" stroke="#999999" />
    </svg>
  );
}
