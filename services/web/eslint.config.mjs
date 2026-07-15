import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FlatCompat } from '@eslint/eslintrc';

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({ baseDirectory: currentDirectory });

const eslintConfig = [
  {
    ignores: ['node_modules/**', '.next/**', 'out/**', 'build/**', 'next-env.d.ts', '*.config.js'],
  },
  ...compat.config({
    parser: '@typescript-eslint/parser',
    plugins: ['@typescript-eslint', 'prettier'],
    parserOptions: {
      createDefaultProgram: true,
    },
    env: {
      browser: true,
      node: true,
      es6: true,
    },
    extends: [
      'next/core-web-vitals',
      'plugin:@typescript-eslint/recommended',
      'plugin:prettier/recommended',
      'prettier',
    ],
    rules: {
      'react/react-in-jsx-scope': 'off',
      'react/jsx-filename-extension': ['warn', { extensions: ['.ts', '.tsx'] }],
      'react/jsx-props-no-spreading': 'off',
      'import/prefer-default-export': 'off',
      'react-hooks/exhaustive-deps': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/naming-convention': 'off',
      'react/require-default-props': 'off',
      'react/no-unstable-nested-components': ['error', { allowAsProps: true }],
      'import/no-cycle': 'off',
      'no-console': 'off',
      'consistent-return': 'error',
      'import/no-extraneous-dependencies': 'error',
      'jsx-a11y/anchor-is-valid': 'error',
      'jsx-a11y/click-events-have-key-events': 'error',
      'no-constant-condition': 'error',
      'no-nested-ternary': 'error',
      'react/no-danger': 'error',
      'react/no-unused-prop-types': 'error',
    },
  }),
];

export default eslintConfig;
