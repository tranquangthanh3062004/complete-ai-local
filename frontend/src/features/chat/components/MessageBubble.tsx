import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Copy, Volume2, Square, Pause, Play, Pin, Share } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface MessageBubbleProps {
  msg: Message;
  isTyping?: boolean;
  
  // TTS Props
  isSpeakingThis?: boolean;
  isPaused?: boolean;
  onSpeak?: (text: string) => void;
  onStopSpeak?: () => void;
  onPauseSpeak?: () => void;
  onResumeSpeak?: () => void;
}

export function MessageBubble({ 
  msg, 
  isTyping, 
  isSpeakingThis,
  isPaused,
  onSpeak,
  onStopSpeak,
  onPauseSpeak,
  onResumeSpeak
}: MessageBubbleProps) {

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={cn(
        "flex gap-3 group",
        msg.role === 'user' ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm border",
        msg.role === 'user'
          ? "bg-gradient-to-br from-slate-100 to-slate-200 border-slate-300 dark:from-slate-700 dark:to-slate-800 dark:border-slate-600"
          : "bg-primary border-primary",
        isSpeakingThis && !isPaused && "animate-pulse shadow-[0_0_15px_rgba(var(--primary),0.5)]"
      )}>
        {msg.role === 'user'
          ? <User size={16} className="text-slate-600 dark:text-slate-300" />
          : <Bot size={16} className="text-primary-foreground" />
        }
      </div>

      {/* Bubble Container */}
      <div className={cn(
        "max-w-[82%] relative flex flex-col",
        msg.role === 'user' ? "items-end" : "items-start"
      )}>
        
        {/* Bubble Text */}
        <div className={cn(
          "px-4 py-3 rounded-2xl",
          msg.role === 'user' ? "bg-primary text-primary-foreground rounded-tr-sm" : "bg-muted rounded-tl-sm",
          isSpeakingThis && "ring-2 ring-primary/50"
        )}>
          {msg.content ? (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
            </div>
          ) : isTyping ? (
            <div className="flex gap-1.5 items-center py-0.5 h-5">
              <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
              <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
              <div className="typing-dot w-1.5 h-1.5 bg-muted-foreground rounded-full" />
            </div>
          ) : null}
        </div>

        {/* Toolbar (Only for Assistant) */}
        {msg.role === 'assistant' && msg.content && (
          <div className="flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleCopy} title="Copy">
              <Copy size={12} className="text-muted-foreground" />
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6" title="Pin">
              <Pin size={12} className="text-muted-foreground" />
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6" title="Share">
              <Share size={12} className="text-muted-foreground" />
            </Button>
            
            {/* Voice Controls */}
            {isSpeakingThis ? (
              <>
                {isPaused ? (
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onResumeSpeak} title="Resume">
                    <Play size={12} className="text-primary" />
                  </Button>
                ) : (
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onPauseSpeak} title="Pause">
                    <Pause size={12} className="text-primary" />
                  </Button>
                )}
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onStopSpeak} title="Stop">
                  <Square size={12} className="text-destructive" />
                </Button>
              </>
            ) : (
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onSpeak?.(msg.content)} title="Speak">
                <Volume2 size={12} className="text-muted-foreground" />
              </Button>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
