import { nextui } from '@nextui-org/theme';

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Gray color
        gray: {
          0.5: '#EBEBEB',
          1: '#E0E0E0',
          2: '#999999',
          3: '#555555',
          4: '#262626',
        },
        // Primary color
        primary: {
          1: '#F5F7FD',
          2: '#96BCFA',
          3: '#191919',
        },
        // Theme color
        theme: {
          alert: '#E63946',
          info: '#D7F963',
        },
        // Dark mode
        dark: {
          b: '#101012',
          l: '#2E2E2E',
          pb: '#1E1E1E',
        },
      },
    },
  },
  darkMode: 'class',
  plugins: [nextui()],
};
