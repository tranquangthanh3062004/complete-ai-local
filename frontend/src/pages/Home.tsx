import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';
import { useChatSSE } from '@/hooks/useChatSSE';
import { useSpeech } from '@/hooks/useSpeech';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageList } from '@/features/chat/components/MessageList';
import { ChatInputBar } from '@/features/chat/components/ChatInputBar';
import html2pdf from 'html2pdf.js';
import { Button } from '@/components/ui/button';
import { Download, LayoutPanelLeft } from 'lucide-react';

export default function Home() {
  const { messages, isStreaming } = useChatStore();
  const { sendMessage } = useChatSSE();
  const [input, setInput] = useState('');
  
  const {
    isListening: isRecording,
    transcript,
    setTranscript,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    pauseSpeaking,
    resumeSpeaking,
    isSpeaking,
    isPaused
  } = useSpeech();

  const [wasVoiceInput, setWasVoiceInput] = useState(false);
  const isStreamingRef = useRef(isStreaming);
  const [activeSpeakId, setActiveSpeakId] = useState<string | null>(null);

  // Auto-fill input with transcript
  useEffect(() => {
    if (isRecording && transcript) {
      setInput(transcript);
    }
  }, [isRecording, transcript]);

  // Handle auto-speak on stream end
  useEffect(() => {
    if (isStreamingRef.current && !isStreaming) {
      if (wasVoiceInput) {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.content) {
          setActiveSpeakId(lastMessage.id);
          speak(lastMessage.content, () => {
            // Continuous Conversation: start listening again automatically after speaking finishes!
            setWasVoiceInput(true);
            startListening();
          });
        }
      }
    }
    isStreamingRef.current = isStreaming;
  }, [isStreaming, wasVoiceInput, messages, speak, startListening]);

  const handleSubmit = () => {
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput('');
    if (isRecording) {
      stopListening();
    }
  };

  const handleSuggestionClick = (label: string) => {
    if (isStreaming) return;
    sendMessage(label);
  };

  const handleToggleRecord = () => {
    if (isSpeaking) {
      stopSpeaking();
    }
    if (isRecording) {
      stopListening();
      if (input.trim()) {
        setWasVoiceInput(true);
        handleSubmit();
      }
    } else {
      setInput('');
      setTranscript('');
      setWasVoiceInput(true);
      startListening();
    }
  };

  const handleSpeak = (id: string, text: string) => {
    setActiveSpeakId(id);
    speak(text, () => setActiveSpeakId(null));
  };

  const handleStopSpeak = () => {
    stopSpeaking();
    setActiveSpeakId(null);
  };

  const exportPDF = () => {
    const element = document.getElementById('chat-container');
    if (element) {
      html2pdf().from(element).save('HNTransit-Chat.pdf');
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] max-w-3xl mx-auto w-full px-4 py-4">
      {/* Top Header Controls */}
      <div className="flex justify-between items-center mb-2 px-2">
        <h2 className="text-sm font-semibold flex items-center gap-2 text-muted-foreground">
          <LayoutPanelLeft size={16} /> Conversation
        </h2>
        <Button variant="outline" size="sm" onClick={exportPDF} className="h-8 text-xs flex gap-1.5">
          <Download size={14} /> Xuất PDF
        </Button>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden glass rounded-2xl shadow-2xl">
        <ScrollArea className="flex-1 px-4 py-5" id="chat-container">
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            onSuggestionClick={handleSuggestionClick}
            activeSpeakId={activeSpeakId}
            isPaused={isPaused}
            onSpeak={handleSpeak}
            onStopSpeak={handleStopSpeak}
            onPauseSpeak={pauseSpeaking}
            onResumeSpeak={resumeSpeaking}
          />
        </ScrollArea>

        <ChatInputBar
          input={input}
          setInput={setInput}
          onSubmit={handleSubmit}
          isStreaming={isStreaming}
          messagesCount={messages.length}
          onSuggestionClick={handleSuggestionClick}
          isRecording={isRecording}
          onToggleRecord={handleToggleRecord}
        />
      </div>
    </div>
  );
}
