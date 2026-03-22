'use client';

import { useState } from 'react';
import { QueryClient, QueryClientProvider as Provider } from '@tanstack/react-query';

export default function QueryClientProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000,
            gcTime: 10 * 60 * 1000,
          },
        },
      }),
  );

  return <Provider client={queryClient}>{children}</Provider>;
}
