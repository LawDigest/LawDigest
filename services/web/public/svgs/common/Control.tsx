'use client';

import { useTheme } from 'next-themes';

export default function IconControl() {
  const { theme } = useTheme();

  return theme === 'dark' ? (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 6H22" stroke="#E0E0E0" strokeWidth="1.3" />
      <path d="M2 12H22" stroke="#E0E0E0" strokeWidth="1.3" />
      <path d="M2 18H22" stroke="#E0E0E0" strokeWidth="1.3" />
      <circle cx="7" cy="6" r="1.35" fill="#101012" stroke="#E0E0E0" strokeWidth="1.3" />
      <circle cx="11" cy="18" r="1.35" fill="#101012" stroke="#E0E0E0" strokeWidth="1.3" />
      <circle cx="17" cy="12" r="1.35" fill="#101012" stroke="#E0E0E0" strokeWidth="1.3" />
    </svg>
  ) : (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 6H22" stroke="black" strokeWidth="1.3" />
      <path d="M2 12H22" stroke="black" strokeWidth="1.3" />
      <path d="M2 18H22" stroke="black" strokeWidth="1.3" />
      <circle cx="7" cy="6" r="1.35" fill="white" stroke="black" strokeWidth="1.3" />
      <circle cx="11" cy="18" r="1.35" fill="white" stroke="black" strokeWidth="1.3" />
      <circle cx="17" cy="12" r="1.35" fill="white" stroke="black" strokeWidth="1.3" />
    </svg>
  );
}
