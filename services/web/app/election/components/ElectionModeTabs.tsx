'use client';

import { Tab, Tabs } from '@nextui-org/tabs';
import { ElectionUiTemplate } from '@/types';

interface ElectionModeTabsProps {
  selectedKey: ElectionUiTemplate;
}

export default function ElectionModeTabs({ selectedKey }: ElectionModeTabsProps) {
  return (
    <section className="w-full">
      <Tabs
        fullWidth
        aria-label="선거 템플릿 모드"
        selectedKey={selectedKey}
        variant="underlined"
        classNames={{
          tabList: 'w-full p-0 border-b border-default-200',
          cursor: 'bg-black',
          tab: 'h-11 px-0',
          tabContent: 'text-sm text-gray-500 group-data-[selected=true]:text-black',
        }}>
        <Tab key="REGIONAL" title="지역별 보기" />
        <Tab
          key="CANDIDATE"
          isDisabled
          title={
            <span className="inline-flex items-center gap-2">
              후보 중심 보기<span className="text-xs">준비 중</span>
            </span>
          }
        />
      </Tabs>
    </section>
  );
}
