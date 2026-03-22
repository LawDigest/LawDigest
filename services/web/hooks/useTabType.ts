import { ValueOf } from '@/types';
import { useState } from 'react';

export function useTabType<T>(defaultValue: ValueOf<T>) {
  const [billType, setBillType] = useState<ValueOf<T>>(defaultValue);

  return [billType, setBillType];
}
