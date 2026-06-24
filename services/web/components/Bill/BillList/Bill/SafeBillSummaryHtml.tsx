import type { CSSProperties, KeyboardEvent, MouseEvent, KeyboardEventHandler, MouseEventHandler } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { renderBillSummaryMarkdown } from './renderBillSummaryMarkdown';

type SafeBillSummaryHtmlProps = {
  ariaLabel: string;
  className: string;
  markdown: string;
  onClick: MouseEventHandler<HTMLDivElement>;
  onKeyDown: KeyboardEventHandler<HTMLDivElement>;
  style: CSSProperties;
};

type TermTooltipState = {
  definition: string;
  left: number;
  top: number;
};

const TOOLTIP_MAX_WIDTH = 280;
const TOOLTIP_VIEWPORT_PADDING = 16;
const TOOLTIP_VERTICAL_OFFSET = 8;
const TERM_TOOLTIP_SELECTOR = '.lawdigest-term-tooltip';

const getTermTooltipElement = (target: EventTarget | null) => {
  if (!(target instanceof Element)) return null;
  return target.closest<HTMLElement>(TERM_TOOLTIP_SELECTOR);
};

export default function SafeBillSummaryHtml({
  ariaLabel,
  className,
  markdown,
  onClick,
  onKeyDown,
  style,
}: SafeBillSummaryHtmlProps) {
  const summaryRef = useRef<HTMLDivElement>(null);
  const [termTooltip, setTermTooltip] = useState<TermTooltipState | null>(null);
  const renderedMarkdown = useMemo(() => renderBillSummaryMarkdown(markdown), [markdown]);
  const isTermTooltipTarget = (target: EventTarget | null) => getTermTooltipElement(target) !== null;

  const showTermTooltip = useCallback((termElement: HTMLElement) => {
    const { definition } = termElement.dataset;
    if (!definition) {
      return;
    }

    const rect = termElement.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const tooltipWidth = Math.min(TOOLTIP_MAX_WIDTH, viewportWidth - TOOLTIP_VIEWPORT_PADDING * 2);
    const centerLeft = rect.left + rect.width / 2;
    const minLeft = TOOLTIP_VIEWPORT_PADDING + tooltipWidth / 2;
    const maxLeft = viewportWidth - TOOLTIP_VIEWPORT_PADDING - tooltipWidth / 2;
    const left = Math.min(Math.max(centerLeft, minLeft), maxLeft);

    setTermTooltip({
      definition,
      left,
      top: rect.bottom + TOOLTIP_VERTICAL_OFFSET,
    });
  }, []);

  const hideTermTooltip = useCallback(() => {
    setTermTooltip(null);
  }, []);

  const handleClick = (event: MouseEvent<HTMLDivElement>) => {
    if (isTermTooltipTarget(event.target)) {
      event.stopPropagation();
      return;
    }
    onClick(event);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (isTermTooltipTarget(event.target)) {
      event.stopPropagation();
      return;
    }
    onKeyDown(event);
  };

  useEffect(() => {
    const termElements = Array.from(summaryRef.current?.querySelectorAll<HTMLElement>(TERM_TOOLTIP_SELECTOR) ?? []);

    const cleanups = termElements.map((termElement) => {
      const handleMouseEnter = () => showTermTooltip(termElement);
      const handleMouseLeave = () => hideTermTooltip();
      const handleFocus = () => showTermTooltip(termElement);
      const handleBlur = () => hideTermTooltip();

      termElement.addEventListener('mouseenter', handleMouseEnter);
      termElement.addEventListener('mouseleave', handleMouseLeave);
      termElement.addEventListener('focus', handleFocus);
      termElement.addEventListener('blur', handleBlur);

      return () => {
        termElement.removeEventListener('mouseenter', handleMouseEnter);
        termElement.removeEventListener('mouseleave', handleMouseLeave);
        termElement.removeEventListener('focus', handleFocus);
        termElement.removeEventListener('blur', handleBlur);
      };
    });

    return () => {
      cleanups.forEach((cleanup) => cleanup());
    };
  }, [hideTermTooltip, renderedMarkdown, showTermTooltip]);

  return (
    <>
      <div
        ref={summaryRef}
        className={className}
        style={style}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-label={ariaLabel}
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: renderedMarkdown }}
      />
      {termTooltip && (
        <div
          className="lawdigest-term-tooltip-layer"
          role="tooltip"
          style={
            {
              ...style,
              '--lawdigest-term-tooltip-left': `${termTooltip.left}px`,
              '--lawdigest-term-tooltip-top': `${termTooltip.top}px`,
            } as CSSProperties
          }>
          {termTooltip.definition}
        </div>
      )}
    </>
  );
}
