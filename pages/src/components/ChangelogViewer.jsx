import React from 'react';
import { ExternalLink, Bug, Sparkles, Rocket, Wrench, ChevronRight } from 'lucide-react';

export function ChangelogViewer({ text }) {
  if (!text) return null;

  // Clean lines
  const lines = text.replace(/\r\n/g, '\n').split('\n');

  const renderFormattedText = (line) => {
    // Replace markdown links [text](url) with clickable <a> tags
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
          className="text-accent hover:underline inline-flex items-center gap-0.5 font-medium"
        >
          {match[1]}
        </a>
      );
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < line.length) {
      parts.push(line.substring(lastIndex));
    }

    // Now format bold text (**text** or `code`) in parts
    return parts.map((part, pIdx) => {
      if (typeof part !== 'string') return part;
      
      // Simple splitter for code `code` and bold **bold**
      const subParts = [];
      const codeRegex = /`([^`]+)`|\*\*([^*]+)\*\*/g;
      let subLast = 0;
      let subMatch;

      while ((subMatch = codeRegex.exec(part)) !== null) {
        if (subMatch.index > subLast) {
          subParts.push(part.substring(subLast, subMatch.index));
        }
        if (subMatch[1]) {
          // code
          subParts.push(
            <code key={subMatch.index} className="px-1.5 py-0.5 rounded bg-muted text-[12px] font-mono text-accent">
              {subMatch[1]}
            </code>
          );
        } else if (subMatch[2]) {
          // bold
          subParts.push(
            <strong key={subMatch.index} className="font-semibold text-foreground">
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
    <div className="space-y-2 text-sm text-foreground/90 font-normal leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1.5" />;

        // Header 2 / 3 (e.g. ## [1.40.0], ### Bug Fixes)
        if (trimmed.startsWith('###') || trimmed.startsWith('##')) {
          const headerText = trimmed.replace(/^#+\s*/, '');
          const isBug = /bug|fix/i.test(headerText);
          const isFeature = /feature|new/i.test(headerText);
          const isSupport = /support|app/i.test(headerText);

          return (
            <div key={idx} className="flex items-center gap-2 pt-3 pb-1 border-b border-border/40 font-semibold text-foreground text-[14px]">
              {isBug && <Bug size={15} className="text-amber-500 shrink-0" />}
              {isFeature && <Sparkles size={15} className="text-emerald-500 shrink-0" />}
              {isSupport && <Rocket size={15} className="text-sky-500 shrink-0" />}
              {!isBug && !isFeature && !isSupport && <Wrench size={15} className="text-accent shrink-0" />}
              <span>{renderFormattedText(headerText)}</span>
            </div>
          );
        }

        // List items (* item or - item)
        if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
          const itemText = trimmed.substring(2);
          return (
            <div key={idx} className="flex items-start gap-2 pl-2 text-[13.5px] text-muted-foreground hover:text-foreground transition-colors">
              <span className="text-accent text-[10px] mt-1.5 shrink-0">●</span>
              <div className="flex-1">{renderFormattedText(itemText)}</div>
            </div>
          );
        }

        // Normal paragraph
        return (
          <p key={idx} className="text-[13.5px] text-muted-foreground">
            {renderFormattedText(trimmed)}
          </p>
        );
      })}
    </div>
  );
}
