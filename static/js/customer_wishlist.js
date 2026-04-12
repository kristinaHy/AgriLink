// Customer Wishlist JavaScript
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
        if (item.href && item.href.includes('wishlist')) {
            item.classList.add('active');
        }
    });
}

function addToCartFromWishlist(itemId) {
    // This would typically make an AJAX call to add to cart
    showToast('Adding item to cart');
    // For now, just show a toast
}

function removeFromWishlist(itemId) {
    // This would typically make an AJAX call to remove from wishlist
    showToast('Removing from wishlist');
    // For now, just show a toast and remove from UI
    const item = document.querySelector(`.wishlist-card[data-id="${itemId}"]`);
    if (item) {
        item.remove();
        refreshWishlistCount();
    }
}

function refreshWishlistCount() {
    // This would update the wishlist badge
    const badge = document.getElementById('wishlistBadge');
    if (badge) {
        const current = parseInt(badge.textContent) || 0;
        const newCount = Math.max(0, current - 1);
        badge.textContent = newCount;
    }
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