import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';
import { useChatSSE } from '@/hooks/useChatSSE';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  SendHorizontal, Bot, User,
  Train, Bus, MapPin, FileText, Star
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
            <div className="flex flex-col items-center justify-center h-full min-h-[380px] text-center space-y-5 animate-slide-up">
              {/* Glowing orb */}
              <div className="relative">
                <div className="absolute inset-0 rounded-3xl bg-primary/30 blur-xl scale-110" />
                <div className="relative w-20 h-20 rounded-3xl bg-gradient-to-br from-primary via-blue-500 to-purple-600 flex items-center justify-center shadow-2xl">
                  <Train size={36} className="text-white" />
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
                    "w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-md",
                    msg.role === 'user'
                      ? "bg-gradient-to-br from-slate-600 to-slate-800"
                      : "bg-gradient-to-br from-primary to-purple-600"
                  )}>
                    {msg.role === 'user'
                      ? <User size={16} className="text-white" />
                      : <Bot size={16} className="text-white" />
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

          <form onSubmit={handleSubmit} className="flex gap-2 items-center">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Nhập câu hỏi về giao thông Hà Nội…"
              disabled={isStreaming}
              className="flex-1 rounded-xl h-11 bg-muted/60 border-border/60 focus:bg-muted focus:border-primary/50 transition-all placeholder:text-muted-foreground/50 text-sm"
            />
            <Button
              type="submit"
              disabled={!input.trim() || isStreaming}
              size="icon"
              className={cn(
                "rounded-xl h-11 w-11 shrink-0 transition-all duration-200 shadow-md",
                input.trim() && !isStreaming
                  ? "bg-gradient-to-br from-primary to-purple-600 hover:shadow-primary/30 hover:shadow-lg scale-100"
                  : "bg-muted text-muted-foreground"
              )}
            >
              <SendHorizontal size={18} />
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
