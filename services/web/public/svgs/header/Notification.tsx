'use client';

import { useTheme } from 'next-themes';

export default function IconNotification() {
  const { theme } = useTheme();

  return theme === 'dark' ? (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M22.5 22.5V12.6419C22.5 8.40781 19.1179 5 15 5C10.8821 5 7.5 8.40781 7.5 12.6419V22.5L22.5 22.5ZM6.55585 23.75L23.4441 23.75C23.617 23.75 23.75 23.6149 23.75 23.4392V12.6419C23.75 7.73648 19.8271 3.75 15 3.75C10.1729 3.75 6.25 7.73648 6.25 12.6419V23.4392C6.25 23.6149 6.38298 23.75 6.55585 23.75Z"
        fill="#999999"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M22.5 22.5V12.6419C22.5 8.40781 19.1179 5 15 5C10.8821 5 7.5 8.40781 7.5 12.6419V22.5L22.5 22.5ZM6.55585 23.75L23.4441 23.75C23.617 23.75 23.75 23.6149 23.75 23.4392V12.6419C23.75 7.73648 19.8271 3.75 15 3.75C10.1729 3.75 6.25 7.73648 6.25 12.6419V23.4392C6.25 23.6149 6.38298 23.75 6.55585 23.75Z"
        fill="black"
        fillOpacity="0.2"
      />
      <rect x="3.75" y="22.5" width="22.5" height="1.25" fill="#999999" />
      <rect x="3.75" y="22.5" width="22.5" height="1.25" fill="black" fillOpacity="0.2" />
      <rect x="7.5" y="25" width="15" height="1.25" fill="#999999" />
      <rect x="7.5" y="25" width="15" height="1.25" fill="black" fillOpacity="0.2" />
    </svg>
  ) : (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M22.5 22.5V12.6419C22.5 8.40781 19.1179 5 15 5C10.8821 5 7.5 8.40781 7.5 12.6419V22.5L22.5 22.5ZM6.55585 23.75L23.4441 23.75C23.617 23.75 23.75 23.6149 23.75 23.4392V12.6419C23.75 7.73648 19.8271 3.75 15 3.75C10.1729 3.75 6.25 7.73648 6.25 12.6419V23.4392C6.25 23.6149 6.38298 23.75 6.55585 23.75Z"
        fill="black"
      />
      <rect x="3.75" y="22.5" width="22.5" height="1.25" fill="black" />
      <rect x="7.5" y="25" width="15" height="1.25" fill="black" />
    </svg>
  );
}
