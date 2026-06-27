import { useCallback, useEffect, useRef, useState } from 'react';
import API_URL, { fetchWithAuth, streamWithAuth } from '../config/api';
import { consumeSSEStream } from '../utils/sse';

// Owns the AI tutor session lifecycle and the per-query SSE streaming pipeline.
// The board is accessed through `getBoard()` which returns the imperative API
// exposed by TutorBoard: { capturePng, injectSvg, clear, hasUserDrawn,
// resetUserDrawn }. The backend request/response contract is unchanged from the
// original AITutorPage.
export function useTutorSession({ currentUser, getBoard, speakSentence, cancelSpeech }) {
  const [sessionId, setSessionId] = useState(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [aiMode, setAiMode] = useState('gemini');

  // Snapshot of the board right after the previous AI turn — used for the
  // backend's annotation diff (what the student drew on top of).
  const previousBoardImageRef = useRef(null);

  const initializeSession = useCallback(async () => {
    if (!currentUser) return;
    try {
      setError(null);
      setIsConnecting(true);
      const response = await fetchWithAuth(`${API_URL}/api/ai-tutor/create-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: currentUser.id, userName: currentUser.name }),
      });
      if (!response.ok) throw new Error('Failed to create session');
      const data = await response.json();
      setSessionId(data.sessionId);
    } catch (err) {
      console.error('Failed to initialize session:', err);
      setError('Failed to connect. Please try again.');
    } finally {
      setIsConnecting(false);
    }
  }, [currentUser]);

  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  const sendQuery = useCallback(
    async (text) => {
      const query = (text || '').trim();
      if (!query || isProcessing) return;

      const board = getBoard();
      const currentImage = board ? await board.capturePng() : null;
      const userDrew = board ? board.hasUserDrawn() : false;
      const isAnnotation = Boolean(userDrew && previousBoardImageRef.current);

      const requestPayload = {
        sessionId,
        query,
        messages,
        canvasImage: currentImage,
        previousCanvasImage: isAnnotation ? previousBoardImageRef.current : null,
        hasAnnotation: isAnnotation,
        mode: aiMode,
      };

      setIsProcessing(true);
      setMessages((prev) => [...prev, { role: 'user', content: query }]);
      cancelSpeech();

      // State local to this streaming turn.
      let assistantContent = '';
      let speechBuffer = '';
      let bubbleAdded = false;

      const appendDelta = (delta) => {
        if (!delta) return;
        assistantContent += delta;

        if (!bubbleAdded) {
          bubbleAdded = true;
          setMessages((prev) => [...prev, { role: 'assistant', content: assistantContent }]);
        } else {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: 'assistant', content: assistantContent };
            return updated;
          });
        }

        // Flush speech on the last sentence boundary so the tutor starts talking
        // as soon as a sentence lands.
        speechBuffer += delta;
        let lastBoundary = -1;
        for (let i = 0; i < speechBuffer.length; i++) {
          const ch = speechBuffer[i];
          if (ch === '.' || ch === '!' || ch === '?') lastBoundary = i;
        }
        if (lastBoundary >= 0) {
          speakSentence(speechBuffer.slice(0, lastBoundary + 1));
          speechBuffer = speechBuffer.slice(lastBoundary + 1);
        }
      };

      const flushRemainingSpeech = () => {
        if (speechBuffer.trim()) speakSentence(speechBuffer);
        speechBuffer = '';
      };

      const showStreamError = (message) => {
        const errText = message || 'Sorry, I encountered an error. Please try again.';
        if (bubbleAdded) {
          assistantContent += `\n\n${errText}`;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: 'assistant', content: assistantContent };
            return updated;
          });
        } else {
          setMessages((prev) => [...prev, { role: 'assistant', content: errText }]);
        }
      };

      const onEvent = (eventName, data) => {
        switch (eventName) {
          case 'text':
            appendDelta(data.delta);
            break;
          case 'svg':
            if (data.svgContent && board) board.injectSvg(data.svgContent);
            break;
          case 'done':
            flushRemainingSpeech();
            break;
          case 'error':
            flushRemainingSpeech();
            showStreamError(data.message);
            break;
          default:
            break;
        }
      };

      try {
        const response = await streamWithAuth(`${API_URL}/api/ai-tutor/process-query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestPayload),
        });
        if (!response.ok || !response.body) throw new Error('Failed to process query');

        await consumeSSEStream(response, onEvent);
        flushRemainingSpeech();

        // The board is now synced with the AI turn; capture it as the new
        // "previous" snapshot and clear the user-drew flag.
        if (board) {
          board.resetUserDrawn();
          setTimeout(async () => {
            previousBoardImageRef.current = await board.capturePng();
          }, 800);
        }
      } catch (err) {
        console.error('Failed to process query:', err);
        flushRemainingSpeech();
        showStreamError();
      } finally {
        setIsProcessing(false);
      }
    },
    [aiMode, cancelSpeech, getBoard, isProcessing, messages, sessionId, speakSentence]
  );

  return {
    sessionId,
    isConnecting,
    error,
    messages,
    isProcessing,
    aiMode,
    setAiMode,
    sendQuery,
    retry: initializeSession,
  };
}
