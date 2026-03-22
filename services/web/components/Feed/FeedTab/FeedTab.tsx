import { Tabs, Tab } from '@nextui-org/tabs';
import { siteConfig } from '@/config/site';
import { FEED_TAB } from '@/constants';
import { Key } from 'react';
import { ValueOf } from '@/types';

export default function FeedTab({
  type,
  clickHandler,
}: {
  type: ValueOf<typeof FEED_TAB>;
  clickHandler: (key: Key) => any;
}) {
  const values = siteConfig.feedTabs;

  return (
    <section className="">
      <Tabs
        fullWidth
        aria-label="Options"
        variant="light"
        classNames={{
          cursor: ['rounded-full bg-black dark:bg-white'],
          tabList: ['gap-0'],
          tab: ['w-[74px] h-[36px] '],
          tabContent:
            'text-base font-medium group-data-[selected=true]:text-white group-data-[selected=true]:dark:text-black',
        }}
        selectedKey={type}
        onSelectionChange={clickHandler}
        className="w-full">
        {values.map(({ label, value }) => (
          <Tab key={FEED_TAB[value as keyof typeof FEED_TAB]} title={label} />
        ))}
      </Tabs>
    </section>
  );
}
