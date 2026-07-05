import { useCallback, useEffect, useRef, useState } from 'react';

// Encapsulates browser speech: sentence-buffered text-to-speech (so the tutor
// starts talking as soon as the first sentence streams in) and one-shot speech
// recognition for voice input. Lifted from the original AITutorPage logic.
export function useSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const recognitionRef = useRef(null);
  const onResultRef = useRef(null);
  const isMutedRef = useRef(false);

  // Initialize speech recognition once.
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (onResultRef.current) onResultRef.current(transcript);
    };
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
  }, []);

  // Cancel any speech on mount and when the component using this unmounts.
  useEffect(() => {
    const cancel = () => {
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    };
    cancel();
    window.addEventListener('beforeunload', cancel);
    return () => {
      cancel();
      window.removeEventListener('beforeunload', cancel);
    };
  }, []);

  // Speak a single sentence. Utterances queue in the browser; isSpeaking stays
  // true until the queue drains.
  const speakSentence = useCallback((sentence) => {
    if (!('speechSynthesis' in window)) return;
    if (isMutedRef.current) return;
    const trimmed = (sentence || '').trim();
    if (!trimmed) return;

    const utterance = new SpeechSynthesisUtterance(trimmed);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onstart = () => setIsSpeaking(true);

    const clearIfDone = () => {
      if (!window.speechSynthesis.speaking && !window.speechSynthesis.pending) {
        setIsSpeaking(false);
      }
    };
    utterance.onend = clearIfDone;
    utterance.onerror = clearIfDone;

    window.speechSynthesis.speak(utterance);
  }, []);

  const cancelSpeech = useCallback(() => {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  const toggleListening = useCallback(
    (onResult) => {
      const recognition = recognitionRef.current;
      if (!recognition) {
        alert('Speech recognition is not supported in your browser.');
        return;
      }
      if (isListening) {
        recognition.stop();
        return;
      }
      onResultRef.current = onResult || null;
      recognition.start();
      setIsListening(true);
    },
    [isListening]
  );

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const next = !prev;
      isMutedRef.current = next;
      if (next && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
      }
      return next;
    });
  }, []);

  return {
    isSpeaking,
    isListening,
    isMuted,
    speakSentence,
    cancelSpeech,
    toggleListening,
    toggleMute,
  };
}
