'use client';

import { useTheme } from 'next-themes';

export default function IconPrev() {
  const { theme } = useTheme();

  return theme === 'dark' ? (
    <svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M13.2031 3.56993L7.49812 9.27493C6.82437 9.94868 6.82437 11.0512 7.49812 11.7249L13.2031 17.4299"
        stroke="white"
        strokeWidth="1.5"
        strokeMiterlimit="10"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ) : (
    <svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M13.2031 3.56993L7.49812 9.27493C6.82437 9.94868 6.82437 11.0512 7.49812 11.7249L13.2031 17.4299"
        stroke="black"
        strokeWidth="1.5"
        strokeMiterlimit="10"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
