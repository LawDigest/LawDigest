'use client';

import { useTheme } from 'next-themes';

export default function IconSearch() {
  const { theme } = useTheme();

  return theme === 'dark' ? (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12.833" cy="12.8335" r="9.85" stroke="#999999" strokeWidth="1.3" />
      <circle cx="12.833" cy="12.8335" r="9.85" stroke="black" strokeOpacity="0.2" strokeWidth="1.3" />
      <path d="M19.833 19.8335L25.6663 25.6668" stroke="#999999" strokeWidth="1.3" />
      <path d="M19.833 19.8335L25.6663 25.6668" stroke="black" strokeOpacity="0.2" strokeWidth="1.3" />
    </svg>
  ) : (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12.833" cy="12.8335" r="9.85" stroke="black" strokeWidth="1.3" />
      <path d="M19.833 19.8335L25.6663 25.6668" stroke="black" strokeWidth="1.3" />
    </svg>
  );
}
