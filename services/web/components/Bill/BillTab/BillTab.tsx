import { Tabs, Tab } from '@nextui-org/tabs';
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
          cursor: 'bg-black dark:bg-white',
          tab: 'px-0 h-10',
          tabContent: 'mx-2 group-data-[selected=true]:text-black group-data-[selected=true]:dark:text-white',
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
