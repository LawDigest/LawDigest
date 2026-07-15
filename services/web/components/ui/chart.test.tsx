import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Bar, BarChart, XAxis } from 'recharts';
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from './chart';

describe('ChartContainer', () => {
  beforeEach(() => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      right: 400,
      bottom: 240,
      left: 0,
      width: 400,
      height: 240,
      toJSON: () => ({}),
    });

    vi.stubGlobal(
      'ResizeObserver',
      class ResizeObserverMock {
        private readonly callback: ResizeObserverCallback;

        constructor(callback: ResizeObserverCallback) {
          this.callback = callback;
        }

        observe(target: Element) {
          this.callback(
            [
              {
                target,
                contentRect: target.getBoundingClientRect(),
              } as ResizeObserverEntry,
            ],
            this as unknown as ResizeObserver,
          );
        }

        disconnect() {}

        unobserve() {}
      },
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('Recharts 3 차트와 커스텀 범례를 렌더링한다', async () => {
    const { container } = render(
      <ChartContainer config={{ count: { label: '법안 수', color: '#96BCFA' } }} style={{ width: 400, height: 240 }}>
        <BarChart data={[{ label: '정치', count: 12 }]}>
          <XAxis dataKey="label" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="count" fill="var(--color-count)" isAnimationActive={false} />
          <ChartLegend content={<ChartLegendContent />} />
        </BarChart>
      </ChartContainer>,
    );

    await waitFor(() => expect(container.querySelector('.recharts-wrapper')).toBeInTheDocument());
    expect(container.querySelector('.recharts-surface')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('법안 수')).toBeInTheDocument());
  });
});
