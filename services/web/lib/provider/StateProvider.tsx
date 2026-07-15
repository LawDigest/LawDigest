'use client';

import { Provider } from 'jotai';

export default function StateProvider({ children }: { children: React.ReactNode }) {
  return <Provider>{children}</Provider>;
}
