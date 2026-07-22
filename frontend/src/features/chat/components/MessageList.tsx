import { useEffect, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import { MessageBubble } from './MessageBubble';
import { WelcomeScreen } from './WelcomeScreen';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  onSuggestionClick: (label: string) => void;
  
  // TTS
  activeSpeakId: string | null;
  isPaused: boolean;
  onSpeak: (id: string, text: string) => void;
  onStopSpeak: () => void;
  onPauseSpeak: () => void;
  onResumeSpeak: () => void;
}

export function MessageList({
  messages,
  isStreaming,
  onSuggestionClick,
  activeSpeakId,
  isPaused,
  onSpeak,
  onStopSpeak,
  onPauseSpeak,
  onResumeSpeak
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  if (messages.length === 0) {
    return <WelcomeScreen onSuggestionClick={onSuggestionClick} />;
  }

  return (
    <div className="space-y-5 pb-2">
      <AnimatePresence initial={false}>
        {messages.map((msg, idx) => {
          const isSpeakingThis = activeSpeakId === msg.id;
          // isTyping is true if it's the last message, from assistant, empty content, and streaming
          const isTyping = isStreaming && idx === messages.length - 1 && msg.role === 'assistant' && !msg.content;
          
          return (
            <MessageBubble
              key={msg.id}
              msg={msg}
              isTyping={isTyping}
              isSpeakingThis={isSpeakingThis}
              isPaused={isPaused}
              onSpeak={(text) => onSpeak(msg.id, text)}
              onStopSpeak={onStopSpeak}
              onPauseSpeak={onPauseSpeak}
              onResumeSpeak={onResumeSpeak}
            />
          );
        })}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
}
