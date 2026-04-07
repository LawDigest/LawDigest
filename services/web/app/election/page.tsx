import { Suspense } from 'react';
import { ElectionMapShell } from './components';

export default function ElectionPage() {
  return (
    <Suspense>
      <ElectionMapShell />
    </Suspense>
  );
}
