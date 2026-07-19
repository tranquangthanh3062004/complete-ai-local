import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';
import { useChatSSE } from '@/hooks/useChatSSE';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  SendHorizontal, Bot, User,
  Train, Bus, MapPin, FileText, Star, Mic, Navigation
} from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';


const HANOI_SUGGESTIONS = [
  { label: "Từ Mỹ Đình lên Hồ Gươm", icon: <Bus size={13}/> },
  { label: "Giá vé Metro Cát Linh - Hà Đông", icon: <Train size={13}/> },
  { label: "Xe buýt đi sân bay Nội Bài", icon: <MapPin size={13}/> },
  { label: "Mức phạt vượt đèn đỏ 2024", icon: <FileText size={13}/> },
  { label: "Vé tháng sinh viên giá bao nhiêu?", icon: <Star size={13}/> },
];

function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shrink-0 shadow-md">
        <Bot size={16} className="text-white" />
      </div>
      <div className="bubble-bot px-4 py-3 flex items-center gap-1.5 h-10">
        <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
        <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
        <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
      </div>
    </div>
  );
}

export default function Home() {
  const { messages, isStreaming } = useChatStore();
  const { sendMessage } = useChatSSE();
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput('');
  };

  const handleSuggestion = (label: string) => {
    if (isStreaming) return;
    sendMessage(label);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] max-w-3xl mx-auto w-full px-4 py-4">
      <div className="flex-1 flex flex-col overflow-hidden glass rounded-2xl shadow-2xl">

        {/* Chat area */}
        <ScrollArea className="flex-1 px-4 py-5">
          {messages.length === 0 ? (
            /* ── Welcome Screen ── */
            <div className="flex flex-col items-center justify-center h-full min-h-[380px] text-center space-y-6 animate-slide-up">
              {/* Transit Hero Graphic */}
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-primary/20 blur-2xl scale-125" />
                <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-xl border-4 border-background/50">
                  <Navigation size={42} className="text-white fill-white/20" />
                </div>
              </div>

              <div className="space-y-1.5">
                <h1 className="text-2xl font-bold tracking-tight">HNTransit AI</h1>
                <p className="text-muted-foreground text-sm max-w-xs">
                  Trợ lý thông minh về giao thông công cộng Hà Nội —<br />
                  xe buýt, metro, lộ trình, luật giao thông
                </p>
              </div>

              {/* Suggestion chips */}
              <div className="flex flex-wrap gap-2 justify-center max-w-sm">
                {HANOI_SUGGESTIONS.map(({ label, icon }) => (
                  <button
                    key={label}
                    className="chip flex items-center gap-1.5"
                    onClick={() => handleSuggestion(label)}
                  >
                    {icon}
                    {label}
                  </button>
                ))}
              </div>

              {/* Badges */}
              <div className="flex gap-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">🚌 120+ tuyến buýt</span>
                <span className="text-border">·</span>
                <span className="flex items-center gap-1">🚇 Metro Hà Nội</span>
                <span className="text-border">·</span>
                <span className="flex items-center gap-1">⚖️ Luật giao thông</span>
              </div>
            </div>
          ) : (
            <div className="space-y-5 pb-2">
              {messages.map((msg, idx) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex gap-3 animate-fade-in",
                    msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                  )}
                  style={{ animationDelay: `${idx * 0.04}s` }}
                >
                  {/* Avatar */}
                  <div className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm border",
                    msg.role === 'user'
                      ? "bg-gradient-to-br from-slate-100 to-slate-200 border-slate-300 dark:from-slate-700 dark:to-slate-800 dark:border-slate-600"
                      : "bg-primary border-primary"
                  )}>
                    {msg.role === 'user'
                      ? <User size={16} className="text-slate-600 dark:text-slate-300" />
                      : <Bot size={16} className="text-primary-foreground" />
                    }
                  </div>

                  {/* Bubble */}
                  <div className={cn(
                    "px-4 py-3 max-w-[82%] group relative",
                    msg.role === 'user' ? "bubble-user text-white" : "bubble-bot"
                  )}>
                    {msg.content ? (
                        <div className="prose prose-sm">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                    ) : (
                      /* Skeleton pulse when content is empty */
                      <div className="flex gap-1.5 items-center py-0.5">
                        <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                        <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                        <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Standalone typing indicator when waiting for first chunk */}
              {isStreaming && messages[messages.length - 1]?.role === 'assistant' && !messages[messages.length - 1]?.content && (
                <TypingIndicator />
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </ScrollArea>

        {/* ── Input bar ─────────────────────────────────────────── */}
        <div className="px-4 py-3 border-t border-border/40">
          {/* Quick chips when chat has started */}
          {messages.length > 0 && !isStreaming && (
            <div className="flex gap-1.5 overflow-x-auto pb-2 scrollbar-hide">
              {HANOI_SUGGESTIONS.slice(0, 3).map(({ label }) => (
                <button
                  key={label}
                  className="chip whitespace-nowrap shrink-0 text-[11px] py-1 px-2.5"
                  onClick={() => handleSuggestion(label)}
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
              {/* Voice Button */}
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setIsRecording(!isRecording)}
                disabled={isStreaming}
                className={cn(
                  "absolute right-1.5 top-1.5 h-9 w-9 rounded-xl transition-all",
                  isRecording 
                    ? "text-destructive hover:text-destructive hover:bg-destructive/10" 
                    : "text-muted-foreground hover:text-primary hover:bg-primary/10"
                )}
              >
                <Mic size={18} className={cn(isRecording && "animate-pulse")} />
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
      </div>
    </div>
  );
}
