import React from 'react';
import { SendHorizontal, Mic, StopCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { HANOI_SUGGESTIONS } from './WelcomeScreen';

interface ChatInputBarProps {
  input: string;
  setInput: (val: string) => void;
  onSubmit: () => void;
  isStreaming: boolean;
  messagesCount: number;
  onSuggestionClick: (label: string) => void;
  
  // Voice
  isRecording: boolean;
  onToggleRecord: () => void;
}

export function ChatInputBar({
  input,
  setInput,
  onSubmit,
  isStreaming,
  messagesCount,
  onSuggestionClick,
  isRecording,
  onToggleRecord
}: ChatInputBarProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <div className="px-4 py-3 border-t border-border/40 bg-background/50 backdrop-blur-sm">
      {messagesCount > 0 && !isStreaming && (
        <div className="flex gap-1.5 overflow-x-auto pb-2 scrollbar-hide">
          {HANOI_SUGGESTIONS.slice(0, 3).map(({ label }) => (
            <button
              key={label}
              className="chip whitespace-nowrap shrink-0 text-[11px] py-1 px-2.5"
              onClick={() => onSuggestionClick(label)}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2 items-end">
        <div className="relative flex-1">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isRecording ? "Đang nghe..." : "Hỏi lộ trình, xe buýt, luật giao thông..."}
            disabled={isStreaming || isRecording}
            className={cn(
              "w-full rounded-2xl min-h-12 bg-muted/60 border-border/60 focus:bg-background focus:border-primary/50 transition-all placeholder:text-muted-foreground/60 text-[15px] pl-4 pr-12 shadow-sm",
              isRecording && "animate-pulse-glow border-primary/50 bg-primary/5"
            )}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onToggleRecord}
            disabled={isStreaming}
            className={cn(
              "absolute right-1.5 top-1.5 h-9 w-9 rounded-xl transition-all",
              isRecording 
                ? "text-destructive hover:text-destructive hover:bg-destructive/10" 
                : "text-muted-foreground hover:text-primary hover:bg-primary/10"
            )}
          >
            {isRecording ? <StopCircle size={18} className="animate-pulse" /> : <Mic size={18} />}
          </Button>
        </div>
        
        <Button
          type="submit"
          disabled={!input.trim() || isStreaming || isRecording}
          size="icon"
          className={cn(
            "rounded-2xl h-12 w-12 shrink-0 transition-all duration-300 shadow-md",
            input.trim() && !isStreaming
              ? "bg-primary text-primary-foreground hover:shadow-primary/30 hover:shadow-lg hover:-translate-y-0.5"
              : "bg-muted text-muted-foreground"
          )}
        >
          <SendHorizontal size={20} />
        </Button>
      </form>

      <p className="text-center text-[10px] text-muted-foreground/50 mt-2">
        HNTransit AI · Thông tin mang tính tham khảo
      </p>
    </div>
  );
}
