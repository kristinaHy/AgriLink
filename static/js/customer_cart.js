// Customer Cart JavaScript
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
        if (item.href && item.href.includes('cart')) {
            item.classList.add('active');
        }
    });
}

function updateQuantity(itemId, newQuantity) {
    if (newQuantity < 1) return;

    // This would typically make an AJAX call to update quantity
    showToast(`Updating quantity to ${newQuantity}`);
    // For now, just show a toast and update UI
    const item = document.querySelector(`.cart-item[data-id="${itemId}"]`);
    if (item) {
        const quantityValue = item.querySelector('.quantity-value');
        if (quantityValue) {
            quantityValue.textContent = newQuantity;
        }
    }
}

function removeFromCart(itemId) {
    // This would typically make an AJAX call to remove item
    showToast('Removing item from cart');
    // For now, just show a toast and remove from UI
    const item = document.querySelector(`.cart-item[data-id="${itemId}"]`);
    if (item) {
        item.remove();
        refreshCartCount();
    }
}

function refreshCartCount() {
    // This would update the cart badge
    const badge = document.getElementById('cartBadge');
    if (badge) {
        const current = parseInt(badge.textContent) || 0;
        const newCount = Math.max(0, current - 1);
        badge.textContent = newCount;
    }
}

function proceedToCheckout() {
    // This would redirect to checkout page
    showToast('Redirecting to checkout...');
    // For now, just show a toast
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