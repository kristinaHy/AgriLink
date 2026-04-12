// Customer Messages JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeUserView();
    setupSidebarActivation();
    setupMessageSearch();
});

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

    searchInput.addEventListener('input', function() {
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

function openConversation(userId) {
    // This would typically load the conversation via AJAX
    showToast(`Opening conversation with user ${userId}`);
    // For now, just show a toast
}

function sendMessage(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const content = formData.get('content');

    if (!content.trim()) return;

    // This would typically send the message via AJAX
    showToast('Sending message...');

    // Clear the input
    form.content.value = '';

    // For demo, add the message to the UI
    addMessageToUI(content, true);
}

function addMessageToUI(content, isSent) {
    const messagesList = document.getElementById('messagesList');
    if (!messagesList) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message-item${isSent ? ' sent' : ' received'}`;

    const now = new Date();
    const timeString = now.toLocaleDateString() + ' ' + now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-time">${timeString}</div>
    `;

    messagesList.appendChild(messageDiv);
    messagesList.scrollTop = messagesList.scrollHeight;
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