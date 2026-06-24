document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatContainer = document.getElementById('chat-container');
    const typingIndicator = document.getElementById('typing-indicator');
    const themeToggle = document.getElementById('theme-toggle');
    const suggestions = document.getElementById('suggestions');

    // Mảng lưu lịch sử chat (để gửi lên API)
    let chatHistory = [];

    // Auto resize input if needed, basic toggle send button
    userInput.addEventListener('input', () => {
        sendBtn.disabled = userInput.value.trim().length === 0;
    });

    // Theme toggle
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.body.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', newTheme);
        themeToggle.innerHTML = `<i data-lucide="${newTheme === 'dark' ? 'moon' : 'sun'}"></i>`;
        lucide.createIcons();
    });

    // Handle form submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        // Hide suggestions after first message
        if (suggestions) suggestions.style.display = 'none';

        // Add user message to UI
        addMessage(text, 'user');
        
        // Add to history
        chatHistory.push({ role: 'user', content: text });
        
        // Clear input
        userInput.value = '';
        sendBtn.disabled = true;

        // Show typing
        typingIndicator.classList.remove('hidden');
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            // Call API
            const response = await fetch('/agents/direct', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: text,
                    messages: chatHistory,
                    model_name: 'gemini',
                    session_id: 'web-pwa-session'
                })
            });

            if (!response.ok) {
                if (response.status === 429) throw new Error("Bạn nhắn hơi nhanh, vui lòng chờ chút nhé!");
                throw new Error("Lỗi kết nối máy chủ");
            }

            const data = await response.json();
            const botText = data.result || "Mình không rõ câu này, bạn hỏi cách khác nhé.";
            
            // Add bot message to UI
            addMessage(botText, 'bot');
            chatHistory.push({ role: 'bot', content: botText });

        } catch (error) {
            addMessage(`⚠️ ${error.message}`, 'bot');
        } finally {
            typingIndicator.classList.add('hidden');
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });

    // Hàm gọi từ Chip gợi ý
    window.sendSuggested = (text) => {
        userInput.value = text;
        sendBtn.disabled = false;
        chatForm.dispatchEvent(new Event('submit'));
    };

    // Hàm định dạng Markdown cơ bản (Bold, List, Line breaks)
    function parseMarkdown(text) {
        let html = text
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Bullets
            .replace(/- (.*?)<br>/g, '<ul><li>$1</li></ul>')
            // Emojis (just keep them)
            ;
        
        // Cleanup nested ul
        html = html.replace(/<\/ul><ul>/g, '');
        return `<p>${html}</p>`;
    }

    // Thêm tin nhắn vào giao diện
    function addMessage(text, sender) {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${sender} slide-in`;

        let avatarHtml = '';
        if (sender === 'bot') {
            avatarHtml = `<div class="avatar"><i data-lucide="bot"></i></div>`;
        } else {
            avatarHtml = `<div class="avatar"><i data-lucide="user"></i></div>`; // Hidden by CSS anyway
        }

        const parsedContent = sender === 'bot' ? parseMarkdown(text) : `<p>${text}</p>`;

        wrapper.innerHTML = `
            ${avatarHtml}
            <div class="message-content glass-card">
                ${parsedContent}
            </div>
        `;

        chatContainer.appendChild(wrapper);
        lucide.createIcons();
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
