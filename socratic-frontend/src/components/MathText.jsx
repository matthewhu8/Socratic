import React from 'react';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

/**
 * Component that renders text containing LaTeX math expressions.
 * Supports both inline math ($...$) and display math ($$...$$).
 */
const MathText = ({ text, className = '' }) => {
  if (!text) return null;

  // Regular expressions to match LaTeX expressions
  const inlineMathRegex = /\$([^\$]+)\$/g;
  const displayMathRegex = /\$\$([^\$]+)\$\$/g;

  // First, handle display math ($$...$$)
  const processDisplayMath = (inputText) => {
    const parts = [];
    let lastIndex = 0;
    let match;

    const regex = new RegExp(displayMathRegex);
    while ((match = regex.exec(inputText)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: inputText.substring(lastIndex, match.index)
        });
      }

      // Add the display math
      parts.push({
        type: 'displayMath',
        content: match[1]
      });

      lastIndex = regex.lastIndex;
    }

    // Add remaining text
    if (lastIndex < inputText.length) {
      parts.push({
        type: 'text',
        content: inputText.substring(lastIndex)
      });
    }

    return parts.length > 0 ? parts : [{ type: 'text', content: inputText }];
  };

  // Then, handle inline math ($...$) within text parts
  const processInlineMath = (parts) => {
    return parts.flatMap((part) => {
      if (part.type !== 'text') return part;

      const subParts = [];
      let lastIndex = 0;
      let match;

      const regex = new RegExp(inlineMathRegex);
      const text = part.content;
      
      while ((match = regex.exec(text)) !== null) {
        // Add text before the match
        if (match.index > lastIndex) {
          subParts.push({
            type: 'text',
            content: text.substring(lastIndex, match.index)
          });
        }

        // Add the inline math
        subParts.push({
          type: 'inlineMath',
          content: match[1]
        });

        lastIndex = regex.lastIndex;
      }

      // Add remaining text
      if (lastIndex < text.length) {
        subParts.push({
          type: 'text',
          content: text.substring(lastIndex)
        });
      }

      return subParts.length > 0 ? subParts : [part];
    });
  };

  // Process the text
  let parts = processDisplayMath(text);
  parts = processInlineMath(parts);

  // Render the parts
  return (
    <span className={className}>
      {parts.map((part, index) => {
        if (part.type === 'text') {
          return <span key={index}>{part.content}</span>;
        } else if (part.type === 'inlineMath') {
          return (
            <InlineMath key={index} math={part.content} />
          );
        } else if (part.type === 'displayMath') {
          return (
            <BlockMath key={index} math={part.content} />
          );
        }
        return null;
      })}
    </span>
  );
};

export default MathText; 