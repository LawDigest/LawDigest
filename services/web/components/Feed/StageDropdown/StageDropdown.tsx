'use client';

import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Button, Selection } from '@nextui-org/react';
import { IconControl } from '@/public/svgs';
import { siteConfig } from '@/config/site';
import { STAGE_TAB, STAGE_TAB_KO } from '@/constants';
import { ValueOf } from '@/types';

export default function StageDropdown({
  type,
  clickHandler,
}: {
  type: ValueOf<typeof STAGE_TAB_KO>;
  clickHandler: (keys: Selection) => any;
}) {
  const stageArray = [{ label: '전체', value: 'all' }];
  const categoryValues = siteConfig.stageTabs;

  return (
    <Dropdown>
      <DropdownTrigger>
        <Button endContent={<IconControl />} className="text-sm font-medium bg-transparent ">
          {type}
        </Button>
      </DropdownTrigger>
      <DropdownMenu
        aria-label="Static Actions"
        variant="flat"
        disallowEmptySelection
        selectionMode="single"
        selectedKeys={type}
        onSelectionChange={(e) => clickHandler(e)}>
        {stageArray.concat(categoryValues).map(({ label, value }) => (
          <DropdownItem key={label} value={label}>
            {STAGE_TAB_KO[value as keyof typeof STAGE_TAB] || '전체'}
          </DropdownItem>
        ))}
      </DropdownMenu>
    </Dropdown>
  );
}
