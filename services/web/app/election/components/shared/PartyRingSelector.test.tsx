// services/web/app/election/components/shared/PartyRingSelector.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PartyRingSelector from './PartyRingSelector';

vi.mock('@/components/common/PartyLogoReplacement/PartyLogoReplacement', () => ({
  default: ({ partyName }: { partyName: string }) => <div>{partyName}</div>,
}));

const PARTIES = [
  { name: '더불어민주당', color: '#152484' },
  { name: '국민의힘', color: '#C9151E' },
];

describe('PartyRingSelector', () => {
  it('정당 목록을 렌더링한다', () => {
    render(<PartyRingSelector parties={PARTIES} selected={null} onSelect={vi.fn()} />);
    expect(screen.getAllByText('더불어민주당').length).toBeGreaterThan(0);
    expect(screen.getAllByText('국민의힘').length).toBeGreaterThan(0);
  });

  it('선택 시 onSelect를 호출한다', () => {
    const onSelect = vi.fn();
    render(<PartyRingSelector parties={PARTIES} selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole('button', { name: /더불어민주당/ }));
    expect(onSelect).toHaveBeenCalledWith('더불어민주당');
  });

  it('이미 선택된 정당을 다시 클릭하면 null을 전달한다', () => {
    const onSelect = vi.fn();
    render(<PartyRingSelector parties={PARTIES} selected="더불어민주당" onSelect={onSelect} />);
    fireEvent.click(screen.getByRole('button', { name: /더불어민주당/ }));
    expect(onSelect).toHaveBeenCalledWith(null);
  });
});
