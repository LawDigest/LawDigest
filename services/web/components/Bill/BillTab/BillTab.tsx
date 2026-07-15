import { Tabs, Tab } from '@heroui/tabs';
import { siteConfig } from '@/config/site';
import { BILL_TAB } from '@/constants';
import { Key } from 'react';
import { ValueOf } from '@/types';

export default function BillTab({
  type,
  clickHandler,
}: {
  type: ValueOf<typeof BILL_TAB>;
  clickHandler: (key: Key) => any;
}) {
  const values = siteConfig.billTabs;

  return (
    <section className="w-full lg:min-w-[840px]">
      <Tabs
        fullWidth
        aria-label="Options"
        variant="underlined"
        classNames={{
          tabList: 'w-full p-0 border-b border-divider',
          cursor: 'bg-primary-3 dark:bg-gray-0.5',
          tab: 'px-0 h-10',
          tabContent: 'mx-2 group-data-[selected=true]:text-primary-3 group-data-[selected=true]:dark:text-gray-0.5',
        }}
        selectedKey={type}
        onSelectionChange={clickHandler}
        className="w-full">
        {values.map(({ label, value }) => (
          <Tab key={BILL_TAB[value as keyof typeof BILL_TAB]} title={label} />
        ))}
      </Tabs>
    </section>
  );
}
