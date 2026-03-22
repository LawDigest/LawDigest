'use client';

import { useEffect, useState } from 'react';
import { useGetBillBookmarkedCount } from '../../apis';

export default function BillBookmarkedCount() {
  const { data } = useGetBillBookmarkedCount();
  const [billCount, setBillCount] = useState(data ? data.data.count : 0);

  useEffect(() => {
    if (data) {
      setBillCount(data.data.count);
    }
  }, [data]);

  return <span className="text-[#555555] dark:text-gray-2">{billCount}</span>;
}
