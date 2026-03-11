import React from "react";

/** Parse **bold** spans within a single line of text. */
function parseBold(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  if (parts.length === 1) return text;
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith("**") && part.endsWith("**") ? (
          <strong key={i} className="font-semibold">
            {part.slice(2, -2)}
          </strong>
        ) : (
          <React.Fragment key={i}>{part}</React.Fragment>
        )
      )}
    </>
  );
}

interface MarkdownMessageProps {
  content: string;
  isUser: boolean;
}

/**
 * Lightweight markdown renderer — no external dependencies.
 * Handles: **bold**, numbered lists, bullet lists, ### headings, paragraphs.
 */
export default function MarkdownMessage({ content, isUser }: MarkdownMessageProps) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let listItems: React.ReactNode[] = [];
  let listType: "ol" | "ul" | null = null;

  const mutedMarker = isUser ? "marker:text-white/60" : "marker:text-zinc-400";

  const flushList = (key: string) => {
    if (!listItems.length) return;
    const items = listItems.splice(0);
    if (listType === "ol") {
      elements.push(
        <ol key={key} className={`md-content ol ${mutedMarker}`}>
          {items}
        </ol>
      );
    } else {
      elements.push(
        <ul key={key} className={`md-content ul ${mutedMarker}`}>
          {items}
        </ul>
      );
    }
    listType = null;
  };

  lines.forEach((line, i) => {
    const olMatch = line.match(/^(\d+)\.\s+(.+)/);
    const ulMatch = line.match(/^[-*]\s+(.+)/);
    const h3Match = line.match(/^###\s+(.+)/);

    if (olMatch) {
      if (listType === "ul") flushList(`flush-${i}`);
      listType = "ol";
      listItems.push(<li key={i}>{parseBold(olMatch[2])}</li>);
    } else if (ulMatch) {
      if (listType === "ol") flushList(`flush-${i}`);
      listType = "ul";
      listItems.push(<li key={i}>{parseBold(ulMatch[1])}</li>);
    } else if (h3Match) {
      flushList(`flush-${i}`);
      elements.push(
        <h3 key={i} className="md-content h3">
          {parseBold(h3Match[1])}
        </h3>
      );
    } else {
      flushList(`flush-${i}`);
      if (line.trim()) {
        elements.push(
          <p key={i} className={elements.length > 0 ? "mt-2" : ""}>
            {parseBold(line)}
          </p>
        );
      }
    }
  });

  flushList("end");

  return <div className="md-content">{elements}</div>;
}
