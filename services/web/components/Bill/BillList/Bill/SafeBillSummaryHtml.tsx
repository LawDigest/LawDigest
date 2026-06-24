import type {
  CSSProperties,
  KeyboardEvent,
  MouseEvent,
  KeyboardEventHandler,
  MouseEventHandler,
  ReactNode,
} from 'react';
import { useState } from 'react';

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
const INLINE_TOKEN_PATTERN = /(\{\{[^:{}\n]+:[^{}\n]+\}\}|<mark>.+?<\/mark>|\*\*.+?\*\*)/g;
const TERM_TOKEN_PATTERN = /^\{\{([^:{}\n]+):([^{}\n]+)\}\}$/;

type RenderTerm = (term: string, definition: string, key: string) => ReactNode;

const parseInlineMarkdown = (value: string, keyPrefix: string, renderTerm: RenderTerm): ReactNode[] => {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let tokenIndex = 0;

  Array.from(value.matchAll(INLINE_TOKEN_PATTERN)).forEach((match) => {
    const token = match[0];
    const index = match.index ?? 0;

    if (index > lastIndex) {
      nodes.push(value.slice(lastIndex, index));
    }

    const key = `${keyPrefix}-${tokenIndex}`;
    const termMatch = token.match(TERM_TOKEN_PATTERN);

    if (termMatch) {
      nodes.push(renderTerm(termMatch[1].trim(), termMatch[2].trim(), key));
    } else if (token.startsWith('<mark>') && token.endsWith('</mark>')) {
      nodes.push(
        <mark className="lawdigest-summary-mark" key={key}>
          {parseInlineMarkdown(token.slice(6, -7), key, renderTerm)}
        </mark>,
      );
    } else if (token.startsWith('**') && token.endsWith('**')) {
      nodes.push(<strong key={key}>{parseInlineMarkdown(token.slice(2, -2), key, renderTerm)}</strong>);
    } else {
      nodes.push(token);
    }

    lastIndex = index + token.length;
    tokenIndex += 1;
  });

  if (lastIndex < value.length) {
    nodes.push(value.slice(lastIndex));
  }

  return nodes;
};

const renderSummaryMarkdown = (markdown: string, renderTerm: RenderTerm) => {
  const nodes: ReactNode[] = [];
  let listItems: ReactNode[] = [];
  let blockId = 0;

  const flushList = () => {
    if (listItems.length === 0) {
      return;
    }

    nodes.push(
      <ul className="lawdigest-summary-list" key={`list-${nodes.length}`}>
        {listItems}
      </ul>,
    );
    listItems = [];
  };

  markdown.split('\n').forEach((line) => {
    const key = `block-${blockId}`;
    blockId += 1;

    if (line.startsWith('- ')) {
      listItems.push(<li key={key}>{parseInlineMarkdown(line.slice(2), key, renderTerm)}</li>);
      return;
    }

    flushList();

    if (line.startsWith('### ')) {
      nodes.push(
        <h3 className="lawdigest-summary-heading mt-4 mb-2 text-base font-semibold" key={key}>
          {parseInlineMarkdown(line.slice(4), key, renderTerm)}
        </h3>,
      );
      return;
    }

    if (line.startsWith('## ')) {
      nodes.push(
        <h2 className="lawdigest-summary-heading mt-5 mb-2 text-lg font-semibold" key={key}>
          {parseInlineMarkdown(line.slice(3), key, renderTerm)}
        </h2>,
      );
      return;
    }

    if (line.trim() !== '') {
      nodes.push(<p key={key}>{parseInlineMarkdown(line, key, renderTerm)}</p>);
    }
  });

  flushList();

  return nodes;
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

  const handleClick = (event: MouseEvent<HTMLDivElement>) => {
    onClick(event);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    onKeyDown(event);
  };

  const renderedMarkdown = renderSummaryMarkdown(markdown, (term, definition, key) => (
    <button
      aria-label={`${term}: ${definition}`}
      className="lawdigest-term-tooltip"
      data-definition={definition}
      key={key}
      onBlur={hideTermTooltip}
      onClick={(event) => event.stopPropagation()}
      onFocus={(event) => showTermTooltip(event.currentTarget)}
      onKeyDown={(event) => event.stopPropagation()}
      onMouseEnter={(event) => showTermTooltip(event.currentTarget)}
      onMouseLeave={hideTermTooltip}
      type="button">
      {term}
    </button>
  ));

  return (
    <>
      <div
        className={className}
        style={style}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-label={ariaLabel}>
        {renderedMarkdown}
      </div>
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
