// Customer Orders JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeUserView();
    setupSidebarActivation();
});

function initializeUserView() {
    const userName = localStorage.getItem('dashboardUserName') || 'Anita Sharma';
    const nameEl = document.getElementById('dashboardUsername');
    if (nameEl) nameEl.textContent = userName;
}

function setupSidebarActivation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.href && item.href.includes('orders')) {
            item.classList.add('active');
        }
    });
}

function viewOrderDetails(orderId) {
    // This would typically open a modal or redirect to order detail page
    showToast(`Viewing details for order #${orderId}`);
    // For now, just show a toast
}

function writeReview(orderId) {
    // This would open a review modal
    showToast(`Opening review form for order #${orderId}`);
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