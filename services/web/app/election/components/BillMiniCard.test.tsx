// services/web/app/election/components/BillMiniCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import BillMiniCard from './BillMiniCard';

describe('BillMiniCard', () => {
  const props = {
    briefSummary: '청년 주거 안정을 위한 공공임대주택 확대 법안',
    billName: '공공주택 특별법 일부개정법률안',
    billStage: '위원회 심사',
    proposeDate: '2026-03-15',
    partyName: '더불어민주당',
  };

  it('briefSummary를 렌더링한다', () => {
    render(<BillMiniCard {...props} />);
    expect(screen.getByText(props.briefSummary)).toBeInTheDocument();
  });

  it('billStage 칩을 렌더링한다', () => {
    render(<BillMiniCard {...props} />);
    expect(screen.getByText('위원회 심사')).toBeInTheDocument();
  });

  it('법안 뱃지를 렌더링한다', () => {
    render(<BillMiniCard {...props} />);
    expect(screen.getByText('법안')).toBeInTheDocument();
  });
});
