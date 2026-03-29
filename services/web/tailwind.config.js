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
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        barGrow: {
          '0%': { transform: 'scaleX(0)' },
          '100%': { transform: 'scaleX(1)' },
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.35s ease-out both',
        'fade-up': 'fadeUp 0.35s ease-out both',
        'slide-in-left': 'slideInLeft 0.3s ease-out both',
        'slide-in-right': 'slideInRight 0.3s ease-out both',
        'bar-grow': 'barGrow 0.4s ease-out 0.28s both',
      },
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
        // Party colors (tokenized from globals.css)
        party: {
          minjoo: '#152484',
          ppp: '#e61e2b',
          jk: '#0073cf',
          reform: '#ff7210',
          jinbo: '#d6001c',
          future: '#45babd',
          basic: '#00d2c3',
          sdp: '#f58400',
          green: '#007c36',
          independent: '#797c85',
          majority: '#2e2e2e',
        },
      },
    },
  },
  darkMode: 'class',
  plugins: [nextui()],
};
