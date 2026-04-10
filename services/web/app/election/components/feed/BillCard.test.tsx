import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import BillCard from './BillCard';

const mockItem = {
  type: 'bill' as const,
  id: 'bill-1',
  briefSummary: '청년 주거 안정을 위한 공공임대주택 확대 법안',
  billName: '공공주택 특별법 일부개정법률안',
  billStage: '위원회 심사',
  proposeDate: '2026-03-15',
  partyName: '더불어민주당',
};

describe('BillCard', () => {
  it('법안 요약을 렌더링한다', () => {
    render(<BillCard item={mockItem} />);
    expect(screen.getByText('청년 주거 안정을 위한 공공임대주택 확대 법안')).toBeInTheDocument();
  });

  it('법안명을 렌더링한다', () => {
    render(<BillCard item={mockItem} />);
    expect(screen.getByText('공공주택 특별법 일부개정법률안')).toBeInTheDocument();
  });

  it('진행 단계를 렌더링한다', () => {
    render(<BillCard item={mockItem} />);
    expect(screen.getByText('위원회 심사')).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<BillCard item={mockItem} />);
    expect(screen.getByText('법안')).toBeInTheDocument();
  });
});
