import { useState, useEffect, useCallback, useRef } from 'react';

// Language mappings for Indian languages
const LANGUAGE_MAP: Record<string, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  kn: 'kn-IN',
  ta: 'ta-IN',
  te: 'te-IN',
  ml: 'ml-IN',
  mr: 'mr-IN',
  bn: 'bn-IN',
  gu: 'gu-IN',
  pa: 'pa-IN',
  or: 'or-IN',
  as: 'as-IN',
  ur: 'ur-IN',
};

type RecognitionState = 'idle' | 'listening' | 'processing' | 'error';

interface UseSpeechRecognitionOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  onResult?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
}

export function useSpeechRecognition({
  language = 'en',
  continuous = false,
  interimResults = true,
  onResult,
  onError,
}: UseSpeechRecognitionOptions = {}) {
  const [isSupported, setIsSupported] = useState(false);
  const [state, setState] = useState<RecognitionState>('idle');
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  
  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);

  useEffect(() => {
    // Check browser support
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.lang = LANGUAGE_MAP[language] || 'en-IN';

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interim = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalTranscript += result[0].transcript;
          } else {
            interim += result[0].transcript;
          }
        }

        if (finalTranscript) {
          setTranscript((prev) => prev + finalTranscript);
          onResult?.(finalTranscript, true);
        }

        setInterimTranscript(interim);
        onResult?.(interim, false);
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setState('error');
        isListeningRef.current = false;
        
        let errorMessage = 'An error occurred';
        switch (event.error) {
          case 'no-speech':
            errorMessage = 'No speech detected. Please try again.';
            break;
          case 'audio-capture':
            errorMessage = 'Microphone not accessible.';
            break;
          case 'not-allowed':
            errorMessage = 'Microphone permission denied.';
            break;
          case 'network':
            errorMessage = 'Network error occurred.';
            break;
          case 'aborted':
            // Silent abort, user stopped
            setState('idle');
            return;
          default:
            errorMessage = `Error: ${event.error}`;
        }
        onError?.(errorMessage);
      };

      recognition.onend = () => {
        if (isListeningRef.current && continuous) {
          // Restart if continuous mode and still meant to be listening
          try {
            recognition.start();
          } catch (e) {
            isListeningRef.current = false;
            setState('idle');
          }
        } else {
          isListeningRef.current = false;
          setState('idle');
        }
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignore
        }
      }
    };
  }, [language, continuous, interimResults, onResult, onError]);

  const start = useCallback(() => {
    if (!isSupported || !recognitionRef.current) return;
    
    try {
      setTranscript('');
      setInterimTranscript('');
      setState('listening');
      isListeningRef.current = true;
      recognitionRef.current.start();
    } catch (e) {
      console.error('Failed to start recognition:', e);
      setState('error');
      onError?.('Failed to start speech recognition');
    }
  }, [isSupported, onError]);

  const stop = useCallback(() => {
    if (!recognitionRef.current) return;
    
    try {
      isListeningRef.current = false;
      recognitionRef.current.stop();
      setState('idle');
    } catch (e) {
      console.error('Failed to stop recognition:', e);
    }
  }, []);

  const reset = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setState('idle');
  }, []);

  return {
    isSupported,
    state,
    transcript,
    interimTranscript,
    start,
    stop,
    reset,
  };
}
