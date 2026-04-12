// Customer Market JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeUserView();
    setupImageFallbacks();
    setupAddToCart();
    setupAddToWishlist();
    setupSidebarActivation();
    setupSearch();
});

function initializeUserView() {
    const userName = localStorage.getItem('dashboardUserName') || 'Anita Sharma';
    const nameEl = document.getElementById('dashboardUsername');
    if (nameEl) nameEl.textContent = userName;
}

function setupImageFallbacks() {
    const images = document.querySelectorAll('.market-card img');
    images.forEach(img => {
        img.addEventListener('error', function() {
            this.src = createFallbackImage(this.alt);
        });
    });
}

function createFallbackImage(title) {
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 300;
    const ctx = canvas.getContext('2d');

    // Background gradient
    const gradient = ctx.createLinearGradient(0, 0, 400, 300);
    gradient.addColorStop(0, '#f0f0f0');
    gradient.addColorStop(1, '#e0e0e0');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 400, 300);

    // Icon
    ctx.fillStyle = '#666';
    ctx.font = '60px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('🛒', 200, 150);

    // Title
    ctx.fillStyle = '#333';
    ctx.font = '20px Arial';
    ctx.fillText(title || 'Product', 200, 200);

    return canvas.toDataURL();
}

function setupAddToCart() {
    const buttons = document.querySelectorAll('.add-cart-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productCard = this.closest('.market-card');
            const productId = productCard?.dataset.id;
            const productName = productCard?.querySelector('h3')?.textContent;
            const priceText = productCard?.querySelector('.price')?.textContent;

            if (productId && productName && priceText) {
                addToCart({
                    id: productId,
                    name: productName,
                    priceText: priceText
                });
            }
        });
    });
}

function addToCart(product) {
    // This would typically make an AJAX call to add to cart
    showToast(`${product.name} added to cart`);
    refreshCartCount();
}

function refreshCartCount() {
    // This would update the cart badge
    const badge = document.getElementById('cartBadge');
    if (badge) {
        // For now, just increment
        const current = parseInt(badge.textContent) || 0;
        badge.textContent = current + 1;
    }
}

function setupAddToWishlist() {
    const buttons = document.querySelectorAll('.wishlist-icon-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productCard = this.closest('.market-card');
            const productId = productCard?.dataset.id;
            const productName = productCard?.querySelector('h3')?.textContent;
            const priceText = productCard?.querySelector('.price')?.textContent;

            if (productId && productName && priceText) {
                addToWishlist({
                    id: productId,
                    name: productName,
                    priceText: priceText
                });
            }
        });
    });
}

function addToWishlist(product) {
    const wishlist = getWishlist();
    const exists = wishlist.some(item => item.id === product.id);

    if (exists) {
        showToast(`${product.name} already in wishlist`);
        return;
    }

    wishlist.push(product);
    saveWishlist(wishlist);
    refreshWishlistCount();
    showToast(`${product.name} added to wishlist`);
}

function getWishlist() {
    const raw = localStorage.getItem('dashboardWishlist');
    if (!raw) return [];

    try {
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
        console.error('Error parsing wishlist:', error);
        return [];
    }
}

function saveWishlist(wishlist) {
    localStorage.setItem('dashboardWishlist', JSON.stringify(wishlist));
}

function refreshWishlistCount() {
    const wishlist = getWishlist();
    const badge = document.getElementById('wishlistBadge');
    if (badge) {
        badge.textContent = wishlist.length;
    }
}

function setupSidebarActivation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.href && item.href.includes('market')) {
            item.classList.add('active');
        }
    });
}

function setupSearch() {
    const searchInput = document.getElementById('marketSearchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        const query = this.value.trim().toLowerCase();
        filterMarket(query);
    });

    filterMarket('');
}

function filterMarket(query) {
    const normalized = query.toLowerCase();
    const products = document.querySelectorAll('.market-card');
    let visibleCount = 0;

    products.forEach(card => {
        const title = card.querySelector('h3')?.textContent.toLowerCase() || '';
        const farmer = card.querySelector('.meta-row')?.textContent.toLowerCase() || '';
        const category = card.dataset.category?.toLowerCase() || '';
        const isVisible = !normalized ||
            title.includes(normalized) ||
            farmer.includes(normalized) ||
            category.includes(normalized);

        card.style.display = isVisible ? 'block' : 'none';
        if (isVisible) visibleCount += 1;
    });
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