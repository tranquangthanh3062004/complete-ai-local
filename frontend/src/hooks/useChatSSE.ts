import { useCallback } from 'react';
import { useChatStore } from '@/store/chatStore';
import { useAuthStore } from '@/store/authStore';

// On Vercel the frontend and backend share the same domain via /api proxy.
// Locally, the backend runs on 8000.
const BASE_URL = import.meta.env.VITE_API_URL || '';

export function useChatSSE() {
  const { addMessage, appendChunk, setStreaming, messages } = useChatStore();
  const token = useAuthStore((state) => state.token);

  const sendMessage = useCallback(async (content: string) => {
    // Add user message
    const userMsgId = crypto.randomUUID();
    addMessage({ id: userMsgId, role: 'user', content, timestamp: new Date() });

    // Add empty bot placeholder
    const botMsgId = crypto.randomUUID();
    addMessage({ id: botMsgId, role: 'assistant', content: '', timestamp: new Date() });
    setStreaming(true);

    // Build recent history (last 6 messages) for context
    const recentMessages = messages.slice(-6).map((m) => ({
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.content,
    }));

    try {
      const endpoint = `${BASE_URL}/api/agents/stream`;

      let sessionId = sessionStorage.getItem('gtcc_session_id');
      if (!sessionId) {
        sessionId = 'web-' + crypto.randomUUID().slice(0, 8);
        sessionStorage.setItem('gtcc_session_id', sessionId);
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query: content,
          messages: recentMessages,
          suggest: true,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        const errText = await response.text().catch(() => '');
        throw new Error(`Server lỗi ${response.status}: ${errText.slice(0, 100)}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');

      if (!reader) throw new Error('Không nhận được dữ liệu từ server');

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process SSE lines
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          // Each block may have multiple "data: " lines
          const dataLines = block
            .split('\n')
            .filter((l) => l.startsWith('data: '))
            .map((l) => l.slice(6));

          const text = dataLines.join('\n');
          if (text && text !== '[DONE]') {
            appendChunk(botMsgId, text);
          }
        }
      }

      // Handle any remaining buffer
      if (buffer.startsWith('data: ')) {
        const remaining = buffer.slice(6);
        if (remaining && remaining !== '[DONE]') {
          appendChunk(botMsgId, remaining);
        }
      }

    } catch (err: any) {
      console.error('[Chat SSE Error]', err);
      appendChunk(
        botMsgId,
        `\n\n**⚠️ Lỗi kết nối:** ${err.message || 'Không thể kết nối với máy chủ.'}`
      );
    } finally {
      setStreaming(false);
    }
  }, [addMessage, appendChunk, setStreaming, messages, token]);

  return { sendMessage };
}
