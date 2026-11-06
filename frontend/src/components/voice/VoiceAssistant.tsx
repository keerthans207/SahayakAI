import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Mic, 
  MicOff, 
  Send, 
  Volume2, 
  VolumeX, 
  RotateCcw,
  Edit2,
  AlertCircle 
} from 'lucide-react';
import { useSpeechRecognition } from '@/hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '@/hooks/useSpeechSynthesis';
import { Button } from '../ui/Button';
import { cn } from '@/lib/utils';

interface VoiceAssistantProps {
  language?: string;
  onSend: (message: string) => void;
  lastAssistantMessage?: string;
  disabled?: boolean;
}

export function VoiceAssistant({ 
  language = 'en', 
  onSend, 
  lastAssistantMessage,
  disabled = false 
}: VoiceAssistantProps) {
  const { t } = useTranslation();
  const [textInput, setTextInput] = useState('');
  const [editableTranscript, setEditableTranscript] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [hasSpoken, setHasSpoken] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    isSupported: speechSupported,
    state: recognitionState,
    transcript,
    interimTranscript,
    start: startListening,
    stop: stopListening,
    reset: resetRecognition,
  } = useSpeechRecognition({
    language,
    interimResults: true,
    onResult: (text, isFinal) => {
      if (isFinal) {
        setEditableTranscript((prev) => prev + text);
      }
    },
    onError: (error) => {
      setErrorMessage(error);
      setTimeout(() => setErrorMessage(''), 5000);
    },
  });

  const {
    isSupported: ttsSupported,
    isSpeaking,
    speak,
    stop: stopSpeaking,
  } = useSpeechSynthesis({
    language,
    onEnd: () => setHasSpoken(true),
  });

  useEffect(() => {
    if (transcript) {
      setEditableTranscript(transcript);
    }
  }, [transcript]);

  const handleMicClick = () => {
    if (recognitionState === 'listening') {
      stopListening();
    } else {
      setErrorMessage('');
      setEditableTranscript('');
      setIsEditing(false);
      resetRecognition();
      startListening();
    }
  };

  const handleSend = () => {
    const message = editableTranscript.trim() || textInput.trim();
    if (message) {
      onSend(message);
      setTextInput('');
      setEditableTranscript('');
      setIsEditing(false);
      resetRecognition();
      setHasSpoken(false);
    }
  };

  const handleTextSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      onSend(textInput.trim());
      setTextInput('');
      setHasSpoken(false);
    }
  };

  const handleSpeakResponse = () => {
    if (lastAssistantMessage && !isSpeaking) {
      speak(lastAssistantMessage, language);
    }
  };

  const handleRepeat = () => {
    if (lastAssistantMessage) {
      stopSpeaking();
      setTimeout(() => speak(lastAssistantMessage, language), 100);
    }
  };

  const isListening = recognitionState === 'listening';
  const hasTranscript = editableTranscript.trim().length > 0;

  if (!speechSupported) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-900">
              {t('voice.notSupported', { defaultValue: 'Voice input not supported' })}
            </p>
            <p className="text-sm text-amber-700 mt-1">
              {t('voice.notSupportedDesc', { 
                defaultValue: 'Your browser doesn\'t support speech recognition. Please use text input or try Chrome/Edge.' 
              })}
            </p>
          </div>
        </div>
        
        {/* Fallback text input */}
        <form onSubmit={handleTextSend} className="mt-4 flex gap-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={t('voice.typeMessage', { defaultValue: 'Type your message...' })}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={disabled}
          />
          <Button type="submit" disabled={!textInput.trim() || disabled}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Voice Controls */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col items-center gap-4">
          {/* Large Microphone Button */}
          <button
            onClick={handleMicClick}
            disabled={disabled}
            className={cn(
              'relative w-20 h-20 rounded-full flex items-center justify-center transition-all transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-offset-2',
              isListening
                ? 'bg-red-500 hover:bg-red-600 focus:ring-red-300 animate-pulse'
                : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-300',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            aria-label={isListening ? t('voice.stopListening') : t('voice.startListening')}
            aria-pressed={isListening}
          >
            {isListening ? (
              <>
                <Mic className="h-10 w-10 text-white" />
                <span className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-75"></span>
              </>
            ) : (
              <Mic className="h-10 w-10 text-white" />
            )}
          </button>

          {/* Status Text */}
          <div className="text-center">
            <p className={cn(
              'font-medium',
              isListening ? 'text-red-600' : 'text-gray-700'
            )}>
              {isListening 
                ? t('voice.listening', { defaultValue: 'Listening...' })
                : t('voice.tapToSpeak', { defaultValue: 'Tap to speak' })
              }
            </p>
            {isListening && (
              <p className="text-sm text-gray-500 mt-1">
                {t('voice.tapToStop', { defaultValue: 'Tap again to stop' })}
              </p>
            )}
          </div>

          {/* Live Transcript */}
          {(interimTranscript || hasTranscript) && (
            <div className="w-full bg-indigo-50 border border-indigo-200 rounded-lg p-4 min-h-[60px]">
              <div className="flex items-start justify-between gap-2 mb-2">
                <p className="text-xs font-medium text-indigo-900">
                  {isListening ? t('voice.recognizing') : t('voice.transcript')}:
                </p>
                {!isListening && hasTranscript && (
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                  >
                    <Edit2 className="h-3 w-3" />
                    {isEditing ? t('common.done') : t('common.edit')}
                  </button>
                )}
              </div>
              
              {isEditing ? (
                <textarea
                  ref={textareaRef}
                  value={editableTranscript}
                  onChange={(e) => setEditableTranscript(e.target.value)}
                  className="w-full bg-white border border-indigo-300 rounded p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[80px]"
                  autoFocus
                />
              ) : (
                <p className="text-sm text-gray-900">
                  {editableTranscript}
                  {interimTranscript && (
                    <span className="text-gray-500 italic"> {interimTranscript}</span>
                  )}
                </p>
              )}
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="w-full bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{errorMessage}</p>
            </div>
          )}

          {/* Send Button */}
          {hasTranscript && !isListening && (
            <Button
              onClick={handleSend}
              size="lg"
              className="w-full gap-2"
              disabled={disabled}
            >
              <Send className="h-5 w-5" />
              {t('voice.sendMessage', { defaultValue: 'Send Message' })}
            </Button>
          )}
        </div>
      </div>

      {/* Text Input Alternative */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <form onSubmit={handleTextSend} className="flex gap-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={t('voice.orTypeHere', { defaultValue: 'Or type your message here...' })}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={disabled}
          />
          <Button type="submit" disabled={!textInput.trim() || disabled} variant="outline">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>

      {/* Response Audio Controls */}
      {lastAssistantMessage && ttsSupported && (
        <div className="bg-violet-50 border border-violet-200 rounded-lg p-4 flex items-center gap-3">
          <div className="flex-1">
            <p className="text-sm font-medium text-violet-900">
              {t('voice.responseAudio', { defaultValue: 'Response Audio' })}
            </p>
            <p className="text-xs text-violet-700 mt-0.5">
              {isSpeaking ? t('voice.speaking') : t('voice.clickToHear')}
            </p>
          </div>
          <div className="flex gap-2">
            {isSpeaking ? (
              <Button
                onClick={stopSpeaking}
                size="sm"
                variant="outline"
                className="gap-2"
              >
                <VolumeX className="h-4 w-4" />
                {t('voice.stop')}
              </Button>
            ) : (
              <>
                <Button
                  onClick={handleSpeakResponse}
                  size="sm"
                  variant="outline"
                  className="gap-2"
                  disabled={disabled}
                >
                  <Volume2 className="h-4 w-4" />
                  {hasSpoken ? t('voice.replay') : t('voice.listen')}
                </Button>
                {hasSpoken && (
                  <Button
                    onClick={handleRepeat}
                    size="sm"
                    variant="ghost"
                    className="gap-2"
                    disabled={disabled}
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
