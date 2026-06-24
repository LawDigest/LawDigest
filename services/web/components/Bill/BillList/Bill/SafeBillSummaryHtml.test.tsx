import { fireEvent, render, screen } from '@testing-library/react';
import type { CSSProperties } from 'react';
import { describe, expect, it, vi } from 'vitest';
import SafeBillSummaryHtml from './SafeBillSummaryHtml';

describe('SafeBillSummaryHtml', () => {
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
});
