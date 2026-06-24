import type { CSSProperties, KeyboardEvent, MouseEvent, KeyboardEventHandler, MouseEventHandler } from 'react';
import { renderBillSummaryMarkdown } from './renderBillSummaryMarkdown';

type SafeBillSummaryHtmlProps = {
  ariaLabel: string;
  className: string;
  markdown: string;
  onClick: MouseEventHandler<HTMLDivElement>;
  onKeyDown: KeyboardEventHandler<HTMLDivElement>;
  style: CSSProperties;
};

export default function SafeBillSummaryHtml({
  ariaLabel,
  className,
  markdown,
  onClick,
  onKeyDown,
  style,
}: SafeBillSummaryHtmlProps) {
  const shouldKeepTooltipOpen = (target: EventTarget | null) =>
    target instanceof Element && Boolean(target.closest('.lawdigest-term-tooltip'));

  const handleClick = (event: MouseEvent<HTMLDivElement>) => {
    if (shouldKeepTooltipOpen(event.target)) {
      event.stopPropagation();
      return;
    }
    onClick(event);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (shouldKeepTooltipOpen(event.target)) {
      event.stopPropagation();
      return;
    }
    onKeyDown(event);
  };

  return (
    <div
      className={className}
      style={style}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={ariaLabel}
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: renderBillSummaryMarkdown(markdown) }}
    />
  );
}
