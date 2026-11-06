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
type ErrorType = 'network' | 'permission-denied' | 'not-allowed' | 'no-speech' | 'audio-capture' | 'unsupported' | 'unknown';

interface UseSpeechRecognitionOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  onResult?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: string, errorType: ErrorType) => void;
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
    const supported = !!SpeechRecognition;
    setIsSupported(supported);

    if (!supported) {
      return;
    }

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
        if (interim) {
          onResult?.(interim, false);
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        
        // Always reset listening state on error
        isListeningRef.current = false;
        setState('error');
        
        let errorMessage = 'An error occurred';
        let errorType: ErrorType = 'unknown';
        
        switch (event.error) {
          case 'no-speech':
            errorMessage = 'No speech detected. Please try again.';
            errorType = 'no-speech';
            // Auto-reset to idle for no-speech (user just didn't speak)
            setTimeout(() => setState('idle'), 2000);
            break;
          case 'audio-capture':
            errorMessage = 'Microphone not accessible. Please check your device.';
            errorType = 'audio-capture';
            break;
          case 'not-allowed':
          case 'permission-denied':
            errorMessage = 'Microphone permission denied. Please allow microphone access in your browser settings.';
            errorType = 'permission-denied';
            break;
          case 'network':
            errorMessage = 'Network error. Speech recognition requires an internet connection.';
            errorType = 'network';
            break;
          case 'aborted':
            // Silent abort, user stopped intentionally
            setState('idle');
            return;
          default:
            errorMessage = `Speech recognition error: ${event.error}`;
            errorType = 'unknown';
        }
        
        onError?.(errorMessage, errorType);
      };

      recognition.onend = () => {
        if (isListeningRef.current && continuous) {
          // Restart if continuous mode and still meant to be listening
          try {
            recognition.start();
          } catch (e) {
            console.error('Failed to restart recognition:', e);
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
    if (!isSupported) {
      onError?.('Speech recognition is not supported in your browser.', 'unsupported');
      return;
    }
    
    if (!recognitionRef.current) {
      onError?.('Speech recognition is not initialized.', 'unsupported');
      return;
    }
    
    try {
      setTranscript('');
      setInterimTranscript('');
      setState('listening');
      isListeningRef.current = true;
      recognitionRef.current.start();
    } catch (e) {
      console.error('Failed to start recognition:', e);
      setState('error');
      isListeningRef.current = false;
      onError?.('Failed to start speech recognition. Please try again.', 'unknown');
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
      setState('idle');
      isListeningRef.current = false;
    }
  }, []);

  const reset = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setState('idle');
    isListeningRef.current = false;
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
