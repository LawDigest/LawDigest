'use client';

import { useTheme } from 'next-themes';

export default function IconEnter() {
  const { theme } = useTheme();

  return theme === 'dark' ? (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M5.56836 12.45L9.64336 8.37505C10.1246 7.8938 10.1246 7.1063 9.64336 6.62505L5.56836 2.55005"
        stroke="white"
        strokeWidth="1.5"
        strokeMiterlimit="10"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ) : (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M5.56836 12.45L9.64336 8.37505C10.1246 7.8938 10.1246 7.1063 9.64336 6.62505L5.56836 2.55005"
        stroke="black"
        strokeWidth="1.5"
        strokeMiterlimit="10"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
