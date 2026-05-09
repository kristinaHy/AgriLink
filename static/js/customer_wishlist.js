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
    const csrftoken = getCookie('csrftoken');
    
    // 1. Add to cart
    fetch(`/cart/add/${itemId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken,
        },
        body: 'quantity=1'
    })
    .then(response => {
        if (response.ok) {
            showToast('Added to cart!');
            // 2. Remove from wishlist
            removeFromWishlist(itemId);
            // Update cart count if needed
            refreshCartCount();
        } else {
            showToast('Failed to add to cart');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to add to cart');
    });
}

function refreshCartCount() {
    const badge = document.getElementById('cartBadge');
    if (badge) {
        fetch('/cart/count/')
        .then(response => response.json())
        .then(data => {
            badge.textContent = data.count;
            badge.style.display = data.count > 0 ? 'flex' : 'none';
        });
    }
}

function removeFromWishlist(itemId) {
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/wishlist/remove/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(data.message);
            const item = document.querySelector(`.market-card[data-id="${itemId}"]`);
            if (item) {
                item.remove();
            }
            refreshWishlistCount(data.count);
            
            // If wishlist is empty, reload to show empty state
            if (data.count === 0) {
                window.location.reload();
            }
        } else {
            showToast(data.message || 'Error removing from wishlist');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to remove from wishlist');
    });
}

function refreshWishlistCount(count) {
    const badge = document.getElementById('wishlistBadge');
    if (badge) {
        badge.textContent = count;
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