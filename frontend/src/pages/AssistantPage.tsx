import React, { useState, useEffect, useRef } from 'react';

import { useTranslation } from 'react-i18next';

import { useLocation, useNavigate } from 'react-router-dom';

import { MessageSquare, Sparkles, Plus, History } from 'lucide-react';

import { Card } from '../components/ui/Card';

import { Button } from '../components/ui/Button';

import { MarkdownRenderer } from '../components/ui/MarkdownRenderer';

import { VoiceAssistant } from '../components/voice/VoiceAssistant';

import { chatService } from '../services/chat.service';

import type { ChatMessageRead } from '../types/api';



interface Message extends ChatMessageRead {

  isStreaming?: boolean;

}



export const AssistantPage: React.FC = () => {

  const { t, i18n } = useTranslation();

  const location = useLocation();

  const navigate = useNavigate();

  const [sessionId, setSessionId] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);

  const [isProcessing, setIsProcessing] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);



  const initialPrompt = (location.state as { initialPrompt?: string })?.initialPrompt;



  // Send message with streaming

  const handleSendMessage = async (content: string) => {

    if (!content.trim() || isProcessing) return;



    const trimmedContent = content.trim();



    // Add user message

    const userMessage: Message = {

      id: `temp-user-${Date.now()}`,

      role: 'user',

      content: trimmedContent,

      created_at: new Date().toISOString(),

    };

    setMessages((prev) => [...prev, userMessage]);

    setIsProcessing(true);



    // Create session if needed

    let activeSessionId = sessionId;

    if (!activeSessionId) {

      try {

        const session = await chatService.createSession({

          title: 'Voice Conversation',

          preferred_language: i18n.language,

        });

        activeSessionId = session.id;

        setSessionId(session.id);

      } catch (error) {

        console.error('Failed to create session:', error);

        setIsProcessing(false);

        return;

      }

    }



    // Add assistant message placeholder

    const assistantMessageId = `temp-assistant-${Date.now()}`;

    const assistantMessage: Message = {

      id: assistantMessageId,

      role: 'assistant',

      content: '',

      created_at: new Date().toISOString(),

      isStreaming: true,

    };

    setMessages((prev) => [...prev, assistantMessage]);



    try {

      // Stream the response

      const stream = chatService.stream(activeSessionId, {

        content: trimmedContent,

        language: i18n.language,

      });



      let fullContent = '';

      for await (const token of stream) {

        fullContent += token;

        setMessages((prev) =>

          prev.map((msg) =>

            msg.id === assistantMessageId

              ? { ...msg, content: fullContent }

              : msg

          )

        );

      }



      // Mark streaming as complete

      setMessages((prev) =>

        prev.map((msg) =>

          msg.id === assistantMessageId

            ? { ...msg, isStreaming: false }

            : msg

        )

      );

    } catch (error) {

      console.error('Failed to stream message:', error);

      // Remove the placeholder message on error

      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId));

    } finally {

      setIsProcessing(false);

    }

  };



  const handleNewConversation = async () => {

    setMessages([]);

    setSessionId(null);



    try {

      const session = await chatService.createSession({

        title: 'Voice Conversation',

        preferred_language: i18n.language,

      });

      setSessionId(session.id);

    } catch (error) {

      console.error('Failed to create new session:', error);

    }

  };



  // Initialize session

  useEffect(() => {

    const initSession = async () => {

      try {

        const session = await chatService.createSession({

          title: 'Voice Conversation',

          preferred_language: i18n.language,

        });

        setSessionId(session.id);



        // If there's an initial prompt, send it

        if (initialPrompt) {

          handleSendMessage(initialPrompt);

        }

      } catch (error) {

        console.error('Failed to initialize session:', error);

      }

    };



    if (!sessionId) {

      initSession();

    }

    // eslint-disable-next-line react-hooks/exhaustive-deps

  }, []); // Only run once on mount



  useEffect(() => {

    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  }, [messages]);



  const suggestedPrompts = [

    "Find scholarships for students with disabilities in Karnataka.",

    "How do I obtain a UDID card?",

    "What documents do I need for disability pension?",

    "Check eligibility for PM-DAKSH scheme.",

    "What benefits can I get as a student with disability?",

    "Find government schemes for education support.",

  ];



  const lastAssistantMessage = messages

    .filter((m) => m.role === 'assistant')

    .pop()?.content;



  return (

    <div className="h-[calc(100vh-4rem)] flex flex-col max-w-6xl mx-auto">

      {/* Header */}

      <div className="bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-t-2xl p-6 flex-shrink-0">

        <div className="flex items-center justify-between">

          <div className="flex items-center gap-3">

            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">

              <Sparkles className="h-6 w-6" />

            </div>

            <div>

              <h1 className="text-2xl font-bold">{t('assistant.title')}</h1>

              <p className="text-violet-100 text-sm">

                {t('assistant.subtitle', { defaultValue: 'Your voice-first guide' })}

              </p>

            </div>

          </div>

          <div className="flex gap-2">

            <Button

              onClick={handleNewConversation}

              variant="ghost"

              size="sm"

              className="text-white hover:bg-white/20 gap-2"

            >

              <Plus className="h-4 w-4" />

              {t('assistant.new', { defaultValue: 'New' })}

            </Button>

          </div>

        </div>

      </div>



      {/* Messages Area */}

      <div className="flex-1 overflow-y-auto bg-gray-50 p-6 space-y-6">

        {messages.length === 0 ? (

          <>

            {/* Welcome Message */}

            <Card className="p-6 bg-white">

              <div className="flex items-start gap-4">

                <div className="w-10 h-10 bg-violet-100 rounded-full flex items-center justify-center flex-shrink-0">

                  <Sparkles className="h-5 w-5 text-violet-600" />

                </div>

                <div className="flex-1">

                  <h2 className="text-lg font-semibold text-gray-900 mb-2">

                    {t('assistant.welcomeTitle', { defaultValue: 'Welcome to Sahayak AI!' })}

                  </h2>

                  <p className="text-gray-600 mb-4">

                    {t('assistant.welcomeMessage', {

                      defaultValue: 'I can help you discover government schemes, check eligibility, and guide you through applications. You can speak to me or type your questions.'

                    })}

                  </p>

                  <div className="space-y-2 text-sm text-gray-600">

                    <p className="flex items-start gap-2">

                      <span className="text-violet-600 mt-0.5">✓</span>

                      <span>{t('assistant.capability1', { defaultValue: 'Find schemes based on your needs' })}</span>

                    </p>

                    <p className="flex items-start gap-2">

                      <span className="text-violet-600 mt-0.5">✓</span>

                      <span>{t('assistant.capability2', { defaultValue: 'Check eligibility requirements' })}</span>

                    </p>

                    <p className="flex items-start gap-2">

                      <span className="text-violet-600 mt-0.5">✓</span>

                      <span>{t('assistant.capability3', { defaultValue: 'Understand application process' })}</span>

                    </p>

                    <p className="flex items-start gap-2">

                      <span className="text-violet-600 mt-0.5">✓</span>

                      <span>{t('assistant.capability4', { defaultValue: 'Get guidance in multiple languages' })}</span>

                    </p>

                  </div>

                </div>

              </div>

            </Card>



            {/* Suggested Prompts */}

            <div>

              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">

                <History className="h-4 w-4" />

                {t('assistant.suggestedPrompts', { defaultValue: 'Try asking:' })}

              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">

                {suggestedPrompts.map((prompt, index) => (

                  <button

                    key={index}

                    onClick={() => handleSendMessage(prompt)}

                    disabled={isProcessing}

                    className="text-left p-4 bg-white border border-gray-200 rounded-lg hover:border-violet-300 hover:shadow-sm transition-all group disabled:opacity-50 disabled:cursor-not-allowed"

                  >

                    <div className="flex items-start gap-2">

                      <MessageSquare className="h-4 w-4 text-violet-600 flex-shrink-0 mt-0.5 opacity-70 group-hover:opacity-100 transition-opacity" />

                      <p className="text-sm text-gray-700">{prompt}</p>

                    </div>

                  </button>

                ))}

              </div>

            </div>

          </>

        ) : (

          <>

            {messages.map((message) => (

              <div

                key={message.id}

                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}

              >

                {message.role === 'assistant' && (

                  <div className="w-8 h-8 bg-violet-100 rounded-full flex items-center justify-center flex-shrink-0">

                    <Sparkles className="h-4 w-4 text-violet-600" />

                  </div>

                )}

                <div

                  className={`max-w-[70%] rounded-2xl px-4 py-3 ${

                    message.role === 'user'

                      ? 'bg-indigo-600 text-white'

                      : 'bg-white border border-gray-200 text-gray-900'

                  }`}

                >

                  {message.role === 'assistant' ? (

                    <MarkdownRenderer

                      content={message.content}

                      className="text-sm prose-p:leading-relaxed prose-headings:text-gray-900"

                    />

                  ) : (

                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                  )}

                  {message.isStreaming && (

                    <span className="inline-block w-2 h-4 bg-violet-600 animate-pulse ml-1"></span>

                  )}

                  <p className={`text-xs mt-2 ${

                    message.role === 'user' ? 'text-indigo-200' : 'text-gray-500'

                  }`}>

                    {new Date(message.created_at).toLocaleTimeString()}

                  </p>

                </div>

                {message.role === 'user' && (

                  <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">

                    <MessageSquare className="h-4 w-4 text-indigo-600" />

                  </div>

                )}

              </div>

            ))}

            {isProcessing && (

              <div className="flex gap-3">

                <div className="w-8 h-8 bg-violet-100 rounded-full flex items-center justify-center flex-shrink-0">

                  <Sparkles className="h-4 w-4 text-violet-600 animate-pulse" />

                </div>

                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">

                  <div className="flex gap-1">

                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>

                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>

                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>

                  </div>

                </div>

              </div>

            )}

            <div ref={messagesEndRef} />

          </>

        )}

      </div>



      {/* Voice Composer */}

      <div className="bg-white border-t border-gray-200 p-6 flex-shrink-0">

        <VoiceAssistant

          language={i18n.language}

          onSend={handleSendMessage}

          lastAssistantMessage={lastAssistantMessage}

          disabled={isProcessing}

        />

      </div>

    </div>

  );

};
