import { fireEvent, render, screen } from '@testing-library/react';
import type { CSSProperties } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import SafeBillSummaryHtml from './SafeBillSummaryHtml';

describe('SafeBillSummaryHtml', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('요약 마크다운을 안전하게 렌더링한다', () => {
    render(
      <SafeBillSummaryHtml
        ariaLabel="법안 요약 더 보기"
        className="summary"
        markdown={'## 쉬운 요약\n- **핵심** 설명\n<script>alert(1)</script>'}
        onClick={() => {}}
        onKeyDown={() => {}}
        style={{ '--lawdigest-summary-accent': '#152484' } as CSSProperties}
      />,
    );

    expect(screen.getByRole('button', { name: '법안 요약 더 보기' })).toHaveClass('summary');
    expect(screen.getByRole('heading', { name: '쉬운 요약', level: 2 })).toBeInTheDocument();
    expect(screen.getByText('핵심')).toBeInTheDocument();
    expect(screen.queryByText('alert(1)', { selector: 'script' })).not.toBeInTheDocument();
    expect(screen.getByText('<script>alert(1)</script>')).toBeInTheDocument();
  });

  it('법령용어 툴팁을 누를 때 요약 토글 이벤트를 실행하지 않는다', () => {
    const onClick = vi.fn();

    render(
      <SafeBillSummaryHtml
        ariaLabel="법안 요약 더 보기"
        className="summary"
        markdown="{{청문:행정청이 처분 전에 의견을 듣는 절차}}"
        onClick={onClick}
        onKeyDown={() => {}}
        style={{ '--lawdigest-summary-accent': '#152484' } as CSSProperties}
      />,
    );

    fireEvent.click(screen.getByText('청문'));

    expect(onClick).not.toHaveBeenCalled();
  });

  it('법령용어 툴팁 레이어를 화면 좌우 여백 안으로 보정한다', () => {
    vi.stubGlobal('innerWidth', 320);

    render(
      <SafeBillSummaryHtml
        ariaLabel="법안 요약 더 보기"
        className="summary"
        markdown="{{변상금:허가 없이 재산을 사용한 사람에게 부과하는 금액}}"
        onClick={() => {}}
        onKeyDown={() => {}}
        style={{ '--lawdigest-summary-accent': '#152484' } as CSSProperties}
      />,
    );

    const term = screen.getByText('변상금');
    vi.spyOn(term, 'getBoundingClientRect').mockReturnValue({
      x: 292,
      y: 120,
      left: 292,
      top: 120,
      right: 316,
      bottom: 140,
      width: 24,
      height: 20,
      toJSON: () => {},
    });

    fireEvent.mouseOver(term);

    expect(screen.getByRole('tooltip')).toHaveStyle({
      '--lawdigest-term-tooltip-left': '164px',
      '--lawdigest-term-tooltip-top': '148px',
    });
  });
});
