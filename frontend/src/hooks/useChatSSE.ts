import { useState, useCallback } from 'react';
import { useChatStore } from '@/store/chatStore';
import { useAuthStore } from '@/store/authStore';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useChatSSE() {
  const { addMessage, appendChunk, setStreaming } = useChatStore();
  const token = useAuthStore((state) => state.token);
  const [error, setError] = useState<string | null>(null);
  
  const sendMessage = useCallback(async (content: string) => {
    setError(null);
    const userMsgId = crypto.randomUUID();
    addMessage({ id: userMsgId, role: 'user', content, timestamp: new Date() });
    
    const botMsgId = crypto.randomUUID();
    addMessage({ id: botMsgId, role: 'assistant', content: '', timestamp: new Date() });
    setStreaming(true);

    try {
      const response = await fetch(`${BASE_URL}/agents/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question: content }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');

      if (!reader) {
        throw new Error('No reader from response body');
      }

      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (dataStr === '[DONE]') {
              break;
            }
            appendChunk(botMsgId, dataStr);
          }
        }
      }
      
    } catch (err: any) {
      console.error('Chat error:', err);
      setError(err.message || 'Lỗi kết nối máy chủ');
      appendChunk(botMsgId, '\n\n**[Lỗi: Không thể nhận phản hồi]**');
    } finally {
      setStreaming(false);
    }
  }, [addMessage, appendChunk, setStreaming, token]);

  return { sendMessage, error };
}
