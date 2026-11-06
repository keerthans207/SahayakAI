import { useState, useEffect, useCallback, useRef } from 'react';



interface UseSpeechSynthesisOptions {

  language?: string;

  onEnd?: () => void;

  onError?: (error: string) => void;

}



export function useSpeechSynthesis({

  language = 'en',

  onEnd,

  onError,

}: UseSpeechSynthesisOptions = {}) {

  const [isSupported, setIsSupported] = useState(false);

  const [isSpeaking, setIsSpeaking] = useState(false);

  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);



  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);



  useEffect(() => {

    const synth = window.speechSynthesis;

    setIsSupported(!!synth);



    if (synth) {

      const loadVoices = () => {

        const voices = synth.getVoices();

        setAvailableVoices(voices);

      };



      loadVoices();



      if (synth.onvoiceschanged !== undefined) {

        synth.onvoiceschanged = loadVoices;

      }

    }



    return () => {

      if (window.speechSynthesis) {

        window.speechSynthesis.cancel();

      }

    };

  }, []);



  const getVoiceForLanguage = useCallback((lang: string): SpeechSynthesisVoice | null => {

    // Language code mappings

    const langMap: Record<string, string[]> = {

      en: ['en-IN', 'en-US', 'en-GB'],

      hi: ['hi-IN'],

      kn: ['kn-IN'],

      ta: ['ta-IN'],

      te: ['te-IN'],

      ml: ['ml-IN'],

      mr: ['mr-IN'],

      bn: ['bn-IN'],

      gu: ['gu-IN'],

      pa: ['pa-IN'],

    };



    const preferredLangs = langMap[lang] || ['en-IN'];



    for (const preferredLang of preferredLangs) {

      const voice = availableVoices.find((v) => v.lang.startsWith(preferredLang));

      if (voice) return voice;

    }



    // Fallback to any voice matching the base language

    const baseVoice = availableVoices.find((v) => v.lang.startsWith(lang));

    if (baseVoice) return baseVoice;



    // Final fallback

    return availableVoices[0] || null;

  }, [availableVoices]);



  const speak = useCallback((text: string, selectedLanguage?: string) => {

    if (!isSupported) {

      onError?.('Speech synthesis not supported');

      return;

    }



    const synth = window.speechSynthesis;



    // Cancel any ongoing speech

    synth.cancel();



    const utterance = new SpeechSynthesisUtterance(text);

    const voice = getVoiceForLanguage(selectedLanguage || language);



    if (voice) {

      utterance.voice = voice;

      utterance.lang = voice.lang;

    } else {

      utterance.lang = selectedLanguage === 'hi' ? 'hi-IN' : 'en-IN';

    }



    utterance.rate = 0.9;

    utterance.pitch = 1.0;

    utterance.volume = 1.0;



    utterance.onstart = () => {

      setIsSpeaking(true);

    };



    utterance.onend = () => {

      setIsSpeaking(false);

      onEnd?.();

    };



    utterance.onerror = (event) => {

      console.error('Speech synthesis error:', event);

      setIsSpeaking(false);

      onError?.(`Speech error: ${event.error}`);

    };



    utteranceRef.current = utterance;

    synth.speak(utterance);

  }, [isSupported, language, getVoiceForLanguage, onEnd, onError]);



  const stop = useCallback(() => {

    if (window.speechSynthesis) {

      window.speechSynthesis.cancel();

      setIsSpeaking(false);

    }

  }, []);



  const pause = useCallback(() => {

    if (window.speechSynthesis && isSpeaking) {

      window.speechSynthesis.pause();

    }

  }, [isSpeaking]);



  const resume = useCallback(() => {

    if (window.speechSynthesis && isSpeaking) {

      window.speechSynthesis.resume();

    }

  }, [isSpeaking]);



  return {

    isSupported,

    isSpeaking,

    availableVoices,

    speak,

    stop,

    pause,

    resume,

  };

}
