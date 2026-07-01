'use client';

import { useState } from 'react';
import ExploreSidebar from './ExploreSidebar';
import ExploreSubTabs from './ExploreSubTabs';
import FieldPanel from './FieldPanel';
import AssemblyPanel from './AssemblyPanel';
import StatsPanel from './StatsPanel';
import { ExploreTab } from './tabs';

export default function ExploreBoard() {
  const [tab, setTab] = useState<ExploreTab>('field');

  return (
    <div className="w-full lg:flex lg:gap-8 lg:px-6 lg:pt-6">
      <ExploreSidebar active={tab} onChange={setTab} />

      <div className="min-w-0 lg:flex-1">
        <ExploreSubTabs active={tab} onChange={setTab} />

        <main className="px-4 pb-28 pt-4 md:px-6 md:pb-16 lg:px-0 lg:pt-0">
          {tab === 'field' && <FieldPanel />}
          {tab === 'assembly' && <AssemblyPanel />}
          {tab === 'stats' && <StatsPanel />}
        </main>
      </div>
    </div>
  );
}
