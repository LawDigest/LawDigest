import type { CSSProperties, KeyboardEventHandler, MouseEventHandler } from 'react';
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
  return (
    <div
      className={className}
      style={style}
      onClick={onClick}
      onKeyDown={onKeyDown}
      role="button"
      tabIndex={0}
      aria-label={ariaLabel}
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: renderBillSummaryMarkdown(markdown) }}
    />
  );
}
