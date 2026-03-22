'use client';

import { useTheme } from 'next-themes';

export default function IconNext() {
  const { theme } = useTheme();

  return theme === 'dark' ? (
    <svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M7.79688 17.4301L13.5019 11.7251C14.1756 11.0513 14.1756 9.94882 13.5019 9.27507L7.79688 3.57007"
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
        d="M7.79688 17.4301L13.5019 11.7251C14.1756 11.0513 14.1756 9.94882 13.5019 9.27507L7.79688 3.57007"
        stroke="black"
        strokeWidth="1.5"
        strokeMiterlimit="10"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
