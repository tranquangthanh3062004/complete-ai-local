document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatContainer = document.getElementById('chat-container');
    const typingIndicator = document.getElementById('typing-indicator');
    const themeToggle = document.getElementById('theme-toggle');
    const clearChatBtn = document.getElementById('clear-chat');
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

    // Clear chat
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            chatHistory = [];
            // Keep only the first welcome message
            const messages = Array.from(chatContainer.querySelectorAll('.message-wrapper, .bot-actions'));
            for (let i = 1; i < messages.length; i++) {
                messages[i].remove();
            }
            if (suggestions) suggestions.style.display = 'flex';
        });
    }

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
            const eventId = data.event_id || null;
            
            // Add bot message to UI
            addMessage(botText, 'bot', eventId);
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

    // Sử dụng thư viện marked.js để parse markdown chuẩn xác hơn
    function parseMarkdown(text) {
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }
        return `<p>${text}</p>`; // Fallback
    }

    // Thêm tin nhắn vào giao diện
    function addMessage(text, sender, eventId = null) {
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
        
        // Add Action Bar if bot
        if (sender === 'bot') {
            const actionBar = document.createElement('div');
            actionBar.className = 'bot-actions slide-in';
            actionBar.innerHTML = `
                <button class="action-btn copy-btn" title="Sao chép"><i data-lucide="copy"></i></button>
                <button class="action-btn thumb-up" title="Hữu ích" data-val="1"><i data-lucide="thumbs-up"></i></button>
                <button class="action-btn thumb-down" title="Chưa chính xác" data-val="-1"><i data-lucide="thumbs-down"></i></button>
            `;
            chatContainer.appendChild(actionBar);
            
            // Event Listeners for actions
            const copyBtn = actionBar.querySelector('.copy-btn');
            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(text);
                const icon = copyBtn.querySelector('i');
                icon.setAttribute('data-lucide', 'check');
                lucide.createIcons();
                setTimeout(() => {
                    icon.setAttribute('data-lucide', 'copy');
                    lucide.createIcons();
                }, 2000);
            });

            if (eventId && eventId > 0) {
                const thumbs = actionBar.querySelectorAll('.thumb-up, .thumb-down');
                thumbs.forEach(btn => {
                    btn.addEventListener('click', async () => {
                        // Reset active
                        thumbs.forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        
                        try {
                            await fetch('/learning/feedback', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    event_id: eventId,
                                    feedback: parseInt(btn.getAttribute('data-val')),
                                    note: ''
                                })
                            });
                        } catch (e) {
                            console.error('Lỗi gửi feedback', e);
                        }
                    });
                });
            } else {
                actionBar.querySelector('.thumb-up').style.display = 'none';
                actionBar.querySelector('.thumb-down').style.display = 'none';
            }
        }

        lucide.createIcons();
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
