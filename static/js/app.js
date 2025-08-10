let isProcessing = false;
let sessionId = null;
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'UTC',
        hour12: false
    }) + ' UTC';
    document.getElementById('current-time').textContent = timeString;
}

setInterval(updateTimestamp, 1000);
updateTimestamp();

// Custom Renderer for Marked.js
const renderer = new marked.Renderer();
renderer.code = (code, language) => {
    if (language === 'json') {
        try {
            const formattedJson = JSON.stringify(JSON.parse(code), null, 2);
            return `<pre class="data-card"><code>${formattedJson}</code></pre>`;
        } catch (e) {
            return `<pre class="data-card"><code>${code}</code></pre>`;
        }
    }
    return `<pre><code class="language-${language}">${code}</code></pre>`;
};

marked.setOptions({ 
    renderer,
    breaks: true,
    gfm: true
});

// Event Listeners
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

window.addEventListener('load', () => messageInput.focus());

function sendSuggestion(text) {
    messageInput.value = text;
    sendMessage();
}

// Core Functions
function typeWriter(element, text, speed = 0.5, isMarkdown = false) {
    let i = 0;
    function type() {
        if (i <= text.length) {
            let current = text.substring(0, i);
            element.innerHTML = isMarkdown ? marked.parse(current) : current;
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}

function addMessage(content, isUser = false) {
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;

    const iconClass = isUser ? 'fa-user-secret' : 'fa-robot';
    const sanitizedContent = isUser ? content.replace(/</g, "&lt;").replace(/>/g, "&gt;") : content;

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas ${iconClass}"></i>
        </div>
        <div class="message-content"></div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const messageContentDiv = messageDiv.querySelector('.message-content');
    if (isUser) {
        messageContentDiv.textContent = sanitizedContent;
    } else {
    typeWriter(messageContentDiv, sanitizedContent, 0.5, true);
    }
}

function showTyping() {
    typingIndicator.style.display = 'block';
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTyping() {
    typingIndicator.style.display = 'none';
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isProcessing) return;

    addMessage(message, true);
    messageInput.value = '';

    isProcessing = true;
    sendBtn.disabled = true;
    showTyping();

    try {
        const requestBody = { message, session_id: sessionId };
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

        const data = await response.json();
        sessionId = data.session_id;
        
        hideTyping();
        addMessage(data.response, false);

    } catch (error) {
        console.error('Error:', error);
        hideTyping();
        addMessage(`**System Error:**\nCould not connect to the assistant. Please check the server and try again.`, false);
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}