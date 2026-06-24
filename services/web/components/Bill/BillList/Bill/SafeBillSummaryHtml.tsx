import type {
  CSSProperties,
  FocusEvent,
  KeyboardEvent,
  MouseEvent,
  PointerEvent,
  KeyboardEventHandler,
  MouseEventHandler,
} from 'react';
import { useMemo, useState } from 'react';
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
  const [termTooltip, setTermTooltip] = useState<TermTooltipState | null>(null);
  const renderedMarkdown = useMemo(() => renderBillSummaryMarkdown(markdown), [markdown]);
  const isTermTooltipTarget = (target: EventTarget | null) => getTermTooltipElement(target) !== null;

  const showTermTooltip = (termElement: HTMLElement) => {
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
  };

  const hideTermTooltip = () => {
    setTermTooltip(null);
  };

  const handleTermPointerOver = (event: PointerEvent<HTMLDivElement>) => {
    const termElement = getTermTooltipElement(event.target);
    if (!termElement) {
      return;
    }

    showTermTooltip(termElement);
  };

  const handleTermPointerOut = (event: PointerEvent<HTMLDivElement>) => {
    const termElement = getTermTooltipElement(event.target);
    if (!termElement) {
      return;
    }

    if (event.relatedTarget instanceof Node && termElement.contains(event.relatedTarget)) {
      return;
    }

    hideTermTooltip();
  };

  const handleFocus = (event: FocusEvent<HTMLDivElement>) => {
    const termElement = getTermTooltipElement(event.target);
    if (termElement) {
      showTermTooltip(termElement);
    }
  };

  const handleBlur = (event: FocusEvent<HTMLDivElement>) => {
    if (isTermTooltipTarget(event.target)) {
      hideTermTooltip();
    }
  };

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

  return (
    <>
      <div
        className={className}
        style={style}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onPointerOver={handleTermPointerOver}
        onPointerOut={handleTermPointerOut}
        onPointerLeave={hideTermTooltip}
        onFocus={handleFocus}
        onBlur={handleBlur}
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
