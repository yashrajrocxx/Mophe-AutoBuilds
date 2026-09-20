import React from 'react';

export function ChangelogViewer({ text }) {
  if (!text) return null;

  const lines = text.replace(/\r\n/g, '\n').split('\n');

  const renderFormattedText = (line) => {
    const parts = [];
    let lastIndex = 0;
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    let match;

    while ((match = linkRegex.exec(line)) !== null) {
      if (match.index > lastIndex) {
        parts.push(line.substring(lastIndex, match.index));
      }
      parts.push(
        <a
          key={match.index}
          href={match[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium underline underline-offset-2 hover:opacity-70"
        >
          {match[1]}
        </a>
      );
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < line.length) {
      parts.push(line.substring(lastIndex));
    }

    return parts.map((part, pIdx) => {
      if (typeof part !== 'string') return part;

      const subParts = [];
      const codeRegex = /`([^`]+)`|\*\*([^*]+)\*\*/g;
      let subLast = 0;
      let subMatch;

      while ((subMatch = codeRegex.exec(part)) !== null) {
        if (subMatch.index > subLast) {
          subParts.push(part.substring(subLast, subMatch.index));
        }
        if (subMatch[1]) {
          subParts.push(
            <code key={subMatch.index} className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">
              {subMatch[1]}
            </code>
          );
        } else if (subMatch[2]) {
          subParts.push(
            <strong key={subMatch.index} className="font-semibold">
              {subMatch[2]}
            </strong>
          );
        }
        subLast = subMatch.index + subMatch[0].length;
      }
      if (subLast < part.length) {
        subParts.push(part.substring(subLast));
      }
      return <React.Fragment key={pIdx}>{subParts}</React.Fragment>;
    });
  };

  return (
    <div className="space-y-2 text-sm leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1.5" />;

        if (trimmed.startsWith('###') || trimmed.startsWith('##')) {
          return (
            <h4 key={idx} className="pt-3 pb-1 border-b border-border font-semibold text-[14px]">
              {renderFormattedText(trimmed.replace(/^#+\s*/, ''))}
            </h4>
          );
        }

        if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-1 text-[13px] text-muted-foreground">
              <span aria-hidden="true" className="mt-[7px] w-1 h-1 rounded-full bg-foreground shrink-0" />
              <div className="flex-1">{renderFormattedText(trimmed.substring(2))}</div>
            </div>
          );
        }

        if (/^\d+\.\s/.test(trimmed)) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-1 text-[13px] text-muted-foreground">
              <span className="font-mono text-xs mt-0.5 shrink-0">{trimmed.split('.')[0]}.</span>
              <div className="flex-1">{renderFormattedText(trimmed.replace(/^\d+\.\s*/, ''))}</div>
            </div>
          );
        }

        return (
          <p key={idx} className="text-[13px] text-muted-foreground">
            {renderFormattedText(trimmed)}
          </p>
        );
      })}
    </div>
  );
}
