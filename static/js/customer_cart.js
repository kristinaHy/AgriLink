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

    const csrftoken = getCookie('csrftoken');
    
    fetch(`/cart/update/${itemId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken,
        },
        body: `quantity=${newQuantity}`
    })
    .then(response => {
        if (response.ok) {
            showToast('Cart updated');
            // Reload page to show updated totals
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast('Failed to update quantity');
        }
    })
    .catch(error => {
        console.error('Error updating quantity:', error);
        showToast('Failed to update quantity');
    });
}

function removeFromCart(itemId) {
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/cart/remove/${itemId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken,
        }
    })
    .then(response => {
        if (response.ok) {
            showToast('Item removed from cart');
            // Reload page to show updated cart
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast('Failed to remove item');
        }
    })
    .catch(error => {
        console.error('Error removing item:', error);
        showToast('Failed to remove item');
    });
}

function refreshCartCount() {
    // This would update the cart badge
    const badge = document.getElementById('cartBadge');
    if (badge) {
        // Fetch cart count from backend API
        fetch('/cart/count/')
        .then(response => response.json())
        .then(data => {
            badge.textContent = String(data.count || 0);
        })
        .catch(error => {
            console.error('Error fetching cart count:', error);
            badge.textContent = '0';
        });
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
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