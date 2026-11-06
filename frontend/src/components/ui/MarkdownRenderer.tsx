import React from 'react';
import ReactMarkdown from 'react-markdown';
import { cn } from '../../lib/utils';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Normalize content by converting escaped newlines to actual newlines.
 * Handles both \n and \r\n sequences that may come from backend serialization.
 * Also handles cases where backend might send raw JSON structure with single or double quotes.
 */
function normalizeNewlines(text: string): string {
  let normalizedText = text;

  // Check if text looks like a Python/JSON structure
  // Patterns: [{'type': 'text', 'text': '...'}] or {"type": "text", "text": "..."}
  const looksLikeStructure = (
    (normalizedText.trim().startsWith("[{") || normalizedText.trim().startsWith("{")) &&
    (normalizedText.includes("'type'") || normalizedText.includes('"type"'))
  );

  if (looksLikeStructure) {
    try {
      // Replace Python single quotes with JSON double quotes for parsing
      const jsonCompatible = normalizedText
        .replace(/'/g, '"')  // Convert single quotes to double quotes
        .replace(/\bTrue\b/g, 'true')   // Python True → JSON true
        .replace(/\bFalse\b/g, 'false') // Python False → JSON false
        .replace(/\bNone\b/g, 'null');  // Python None → JSON null

      const parsed = JSON.parse(jsonCompatible);
      
      // Handle list of content blocks: [{"type": "text", "text": "..."}]
      if (Array.isArray(parsed)) {
        normalizedText = parsed
          .filter((block: any) => block && typeof block === 'object' && block.type === 'text')
          .map((block: any) => block.text || '')
          .join('');
      }
      // Handle single content block: {"type": "text", "text": "..."}
      else if (parsed && typeof parsed === 'object' && parsed.type === 'text') {
        normalizedText = parsed.text || '';
      }
    } catch (e) {
      // Not valid structure, continue with text processing
      console.warn('Could not parse structure, treating as plain text:', e);
    }
  }

  // Replace escaped newline sequences with actual newlines
  return normalizedText
    .replace(/\\r\\n/g, '\n')  // Windows-style escaped
    .replace(/\\n/g, '\n')      // Unix-style escaped
    .replace(/\\r/g, '\n');     // Old Mac-style escaped
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className,
}) => {
  // Normalize newlines before rendering
  const normalizedContent = normalizeNewlines(content);

  return (
    <div className={cn('prose prose-sm max-w-none', className)}>
      <ReactMarkdown
        components={{
          h1: ({ node, ...props }) => (
            <h1 className="text-2xl font-bold mb-4 mt-6" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-xl font-bold mb-3 mt-5" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-lg font-semibold mb-2 mt-4" {...props} />
          ),
          p: ({ node, ...props }) => <p className="mb-3" {...props} />,
          ul: ({ node, ...props }) => <ul className="list-disc ml-5 mb-3" {...props} />,
          ol: ({ node, ...props }) => <ol className="list-decimal ml-5 mb-3" {...props} />,
          li: ({ node, ...props }) => <li className="mb-1" {...props} />,
          code: ({ node, ...props }) => (
            <code className="bg-gray-100 rounded px-1 py-0.5 text-sm" {...props} />
          ),
          a: ({ node, ...props }) => (
            <a className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
          ),
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-gray-900" {...props} />
          ),
          em: ({ node, ...props }) => (
            <em className="italic" {...props} />
          ),
        }}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  );
};
