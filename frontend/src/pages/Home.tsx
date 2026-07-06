import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';
import { useChatSSE } from '@/hooks/useChatSSE';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { SendHorizontal, Bot, User, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const { messages, isStreaming } = useChatStore();
  const { sendMessage } = useChatSSE();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    
    sendMessage(input.trim());
    setInput('');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto w-full p-4">
      <Card className="flex-1 flex flex-col overflow-hidden bg-background border-border shadow-sm">
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          <div className="space-y-6">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground mt-20 space-y-4">
                <Bot className="w-16 h-16 opacity-20" />
                <h2 className="text-xl font-medium">GTCC Bot</h2>
                <p className="text-sm">Hỏi tôi về tuyến xe buýt, metro hoặc luật giao thông</p>
                <div className="flex gap-2 mt-4 flex-wrap justify-center">
                  {["Từ Bến Thành đi Suối Tiên", "Giá vé Metro số 1", "Mức phạt vượt đèn đỏ"].map(q => (
                    <Button key={q} variant="outline" size="sm" onClick={() => { setInput(q); }}>
                      {q}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex gap-4",
                  msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                )}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                  msg.role === 'user' ? "bg-primary text-primary-foreground" : "bg-muted"
                )}>
                  {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                </div>
                <div className={cn(
                  "px-4 py-3 rounded-2xl max-w-[85%]",
                  msg.role === 'user' 
                    ? "bg-primary text-primary-foreground" 
                    : "bg-muted text-foreground"
                )}>
                  <div className="prose prose-sm dark:prose-invert break-words">
                    {msg.content ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Loader2 className="w-4 h-4 animate-spin opacity-50" />
                        <span className="opacity-50 text-sm">Đang suy nghĩ...</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="p-4 bg-background border-t">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Nhập câu hỏi của bạn..."
              disabled={isStreaming}
              className="flex-1 rounded-full px-6"
            />
            <Button 
              type="submit" 
              disabled={!input.trim() || isStreaming}
              size="icon"
              className="rounded-full shrink-0 h-10 w-10"
            >
              <SendHorizontal size={18} />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
