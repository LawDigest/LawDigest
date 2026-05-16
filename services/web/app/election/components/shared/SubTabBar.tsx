'use client';

import { Tabs, Tab } from '@nextui-org/tabs';
import { Key } from 'react';

interface SubTab<T extends string> {
  key: T;
  label: string;
}

interface SubTabBarProps<T extends string> {
  tabs: SubTab<T>[];
  active: T;
  onChange: (key: T) => void;
}

export default function SubTabBar<T extends string>({ tabs, active, onChange }: SubTabBarProps<T>) {
  return (
    <div className="px-4 py-2">
      <Tabs
        aria-label="서브 탭"
        variant="light"
        selectedKey={active}
        onSelectionChange={(key: Key) => onChange(key as T)}
        classNames={{
          cursor: 'rounded-full bg-primary-3 dark:bg-gray-0.5',
          tabList: 'gap-0',
          tab: 'h-[32px] px-3.5',
          tabContent:
            'text-sm font-semibold text-gray-2 group-data-[selected=true]:text-white group-data-[selected=true]:dark:text-black',
        }}>
        {tabs.map(({ key, label }) => (
          <Tab key={key} title={label} />
        ))}
      </Tabs>
    </div>
  );
}
