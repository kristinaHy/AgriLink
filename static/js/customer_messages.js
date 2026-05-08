// Customer Messages JavaScript
/* global showToast */

document.addEventListener('DOMContentLoaded', function () {
    initializeUserView();
    setupSidebarActivation();
    setupMessageSearch();
    initializeMessaging();
});

let currentOtherUserId = null;
let currentUserId = null; // We need to know who we are to render messages correctly
let chatSocket = null;

const API_BASE = '/api/messages';
const CONVERSATIONS_URL = `${API_BASE}/conversations/`;
const SEND_URL = `${API_BASE}/send/`;
const CONVERSATION_URL = (otherUserId) => `${API_BASE}/conversation/${otherUserId}/`;

function initializeMessaging() {
    const messageForm = document.getElementById('messageForm');
    
    // Connect to WebSocket
    connectWebSocket();

    if (!messageForm) {
        return;
    }

    // If a server-rendered conversation exists, load it via API (marks incoming as read)
    const receiverInput = messageForm.querySelector('input[name="receiver_id"]');
    if (receiverInput && receiverInput.value) {
        currentOtherUserId = receiverInput.value;
        refreshConversations()
            .then(() => openConversation(currentOtherUserId))
            .catch(() => {});
        return;
    }

    refreshConversations().catch(() => {});
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // The consumer uses self.scope["user"], so the ID in URL doesn't strictly matter but we pass 'me'
    chatSocket = new WebSocket(`${protocol}//${window.location.host}/ws/chat/me/`);

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'chat_message') {
            handleIncomingMessage(data);
        }
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
        // Optional: attempt reconnect here
    };
}

function handleIncomingMessage(data) {
    // data has id, message, sender_id, receiver_id, sender_name, created_at, negotiated_price
    // If we are currently chatting with this person
    const isFromOther = String(data.sender_id) === String(currentOtherUserId);
    const isToOther = String(data.receiver_id) === String(currentOtherUserId);
    
    if (isFromOther || isToOther) {
        const messagesList = document.getElementById('messagesList');
        if (messagesList) {
            const isSentByMe = String(data.sender_id) !== String(currentOtherUserId);
            const item = document.createElement('div');
            item.className = `message-item${isSentByMe ? ' sent' : ' received'}`;
            
            const time = formatBackendTime(data.created_at);
            
            item.innerHTML = `
                <div class="message-content">${escapeHtml(data.message)}</div>
                <div class="message-time">${escapeHtml(time)}</div>
            `;
            messagesList.appendChild(item);
            messagesList.scrollTop = messagesList.scrollHeight;
        }
    }

    // Refresh conversation list to update previews
    refreshConversations().catch(() => {});
}

function initializeUserView() {
    const userName = localStorage.getItem('dashboardUserName') || 'Anita Sharma';
    const nameEl = document.getElementById('dashboardUsername');
    if (nameEl) nameEl.textContent = userName;
}

function setupSidebarActivation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.href && item.href.includes('messages')) {
            item.classList.add('active');
        }
    });
}

function setupMessageSearch() {
    const searchInput = document.getElementById('messageSearch');
    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        filterConversations(query);
    });
}

function filterConversations(query) {
    const conversations = document.querySelectorAll('.conversation-item');
    conversations.forEach(conv => {
        const name = conv.querySelector('.conversation-name')?.textContent.toLowerCase() || '';
        const preview = conv.querySelector('.conversation-preview')?.textContent.toLowerCase() || '';
        const isVisible = !query || name.includes(query) || preview.includes(query);
        conv.style.display = isVisible ? 'flex' : 'none';
    });
}

function getCSRFToken() {
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput && csrfInput.value) return csrfInput.value;

    // Fallback to cookie-based CSRF for any other templates
    const name = 'csrftoken';
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith(name + '=')) {
            return decodeURIComponent(trimmed.substring(name.length + 1));
        }
    }
    return '';
}

async function refreshConversations() {
    const list = document.querySelector('.conversations-list');
    if (!list) return;

    const res = await fetch(CONVERSATIONS_URL, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin'
    });

    if (!res.ok) throw new Error('Failed to load conversations');

    const data = await res.json();
    const conversations = Array.isArray(data.conversations) ? data.conversations : [];

    renderConversations(conversations);

    const unreadTotal = conversations.reduce((sum, c) => sum + (Number(c.unread_count) || 0), 0);
    const badge = document.querySelector('.nav-item.active .nav-badge');
    if (badge) {
        badge.textContent = unreadTotal > 0 ? String(unreadTotal) : '';
        if (!unreadTotal) badge.style.display = 'none';
        else badge.style.display = 'inline-block';
    }
}

function renderConversations(conversations) {
    const list = document.querySelector('.conversations-list');
    if (!list) return;

    if (!conversations.length) {
        list.innerHTML = `
            <div class="no-conversations">
                <p>No messages yet</p>
                <p>Start a conversation with a farmer!</p>
            </div>
        `;
        return;
    }

    const itemsHtml = conversations.map(c => {
        const other = c.other_user || {};
        const otherId = other.id;
        const unreadCount = Number(c.unread_count) || 0;
        const isUnread = unreadCount > 0;

        const timeIso = c.last_message?.created_at;
        const timeText = timeIso ? new Date(timeIso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '';

        const preview = c.last_message?.content_preview || '';

        const displayName = other.name || otherId || 'Unknown';

        const activeClass = currentOtherUserId && String(otherId) === String(currentOtherUserId) ? ' active' : '';
        return `
            <div class="conversation-item${isUnread ? ' unread' : ''}${activeClass}" onclick="openConversation(${otherId})" data-other-user-id="${otherId}">
                <div class="conversation-avatar">${String(displayName).slice(0, 2).toUpperCase()}</div>
                <div class="conversation-info">
                    <div class="conversation-name">${escapeHtml(displayName)}</div>
                    <div class="conversation-preview">${escapeHtml(preview)}</div>
                    <div class="conversation-time">${escapeHtml(timeText)}</div>
                </div>
                ${isUnread ? '<div class="unread-indicator"></div>' : ''}
            </div>
        `;
    }).join('');

    list.innerHTML = itemsHtml;

    // Re-apply search filter if the user already typed something
    const searchInput = document.getElementById('messageSearch');
    if (searchInput && searchInput.value.trim()) {
        filterConversations(searchInput.value.trim().toLowerCase());
    }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = String(str ?? '');
    return div.innerHTML;
}

function ensureThreadVisible() {
    const empty = document.querySelector('.no-conversation-selected');
    if (empty) empty.style.display = 'none';
}

function getThreadHeaderElements() {
    return {
        avatarEl: document.querySelector('.thread-avatar'),
        nameEl: document.querySelector('.thread-info h4'),
        roleEl: document.querySelector('.thread-info p')
    };
}

function formatBackendTime(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    if (Number.isNaN(d.getTime())) return isoString;
    return d.toLocaleString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

async function openConversation(userId) {
    const messagesList = document.getElementById('messagesList');
    const messageForm = document.getElementById('messageForm');
    if (!messagesList || !messageForm) {
        // If the page didn't have server-rendered thread, user will need to refresh.
        // We still attempt to load conversations; the send flow will work once thread exists.
        return;
    }

    currentOtherUserId = String(userId);

    // Update receiver_id hidden field for subsequent sends
    const receiverInput = messageForm.querySelector('input[name="receiver_id"]');
    if (receiverInput) receiverInput.value = currentOtherUserId;

    ensureThreadVisible();

    const res = await fetch(CONVERSATION_URL(userId), {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin'
    });

    if (!res.ok) throw new Error('Failed to load conversation');

    const data = await res.json();
    const conversation = data.conversation || {};
    const otherUser = conversation.other_user || {};
    const messages = Array.isArray(conversation.messages) ? conversation.messages : [];

    const { avatarEl, nameEl, roleEl } = getThreadHeaderElements();
    if (avatarEl) avatarEl.textContent = String(otherUser.name || otherUser.id || '').slice(0, 2).toUpperCase();
    if (nameEl) nameEl.textContent = otherUser.name || 'Unknown';
    if (roleEl) roleEl.textContent = otherUser.role ? String(otherUser.role).toUpperCase() : (otherUser.type ? String(otherUser.type) : '');

    // Render messages (old DOM is replaced)
    messagesList.innerHTML = '';
    messages.forEach(m => {
        const senderId = String(m.sender_id);
        const otherId = String(userId);
        const isSent = senderId !== otherId;

        const item = document.createElement('div');
        item.className = `message-item${isSent ? ' sent' : ' received'}`;

        const content = m.content || '';
        const time = formatBackendTime(m.created_at);

        item.innerHTML = `
            <div class="message-content">${escapeHtml(content)}</div>
            <div class="message-time">${escapeHtml(time)}</div>
        `;
        messagesList.appendChild(item);
    });

    messagesList.scrollTop = messagesList.scrollHeight;

    // Keep badge previews consistent
    refreshConversations().catch(() => {});
}

async function sendMessage(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const receiverId = formData.get('receiver_id');
    const content = String(formData.get('content') || '').trim();
    const subject = String(formData.get('subject') || '').trim();

    if (!receiverId) {
        showToast('Choose a conversation first');
        return;
    }
    if (!content) return;

    // Send via WebSocket if open
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'message': content,
            'receiver_id': receiverId,
            'subject': subject || ''
        }));
        
        const contentEl = form.querySelector('textarea[name="content"]');
        if (contentEl) contentEl.value = '';
        return;
    }

    // Fallback to REST API
    const csrfToken = getCSRFToken();

    const res = await fetch(SEND_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'Accept': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            receiver_id: Number(receiverId),
            subject: subject || '',
            content
        })
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) {
        showToast(data?.message || 'Failed to send message');
        return;
    }

    // Clear input
    const contentEl = form.querySelector('textarea[name="content"]');
    if (contentEl) contentEl.value = '';

    showToast('Message sent');

    // Reload thread from backend (ensures UI/read states are consistent)
    await openConversation(receiverId);
}

function showToast(message) {
    let toast = document.getElementById('dashboardToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'dashboardToast';
        toast.className = 'toast';
        toast.setAttribute('aria-live', 'polite');
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
