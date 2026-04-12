// Customer Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeUserView();
    setupRevealAnimation();
    setupWishlistActions();
    setupSearch();
    refreshDashboardCounts();
    animateStats();
});

// User View Initialization
function initializeUserView() {
    const userName = resolveUserName();
    const shortName = userName.split(' ')[0];
    localStorage.setItem('dashboardIsLoggedIn', 'true');

    const nameEl = document.getElementById('dashboardUsername');
    const status = document.getElementById('dashboardUserStatus');
    const subtitle = document.getElementById('dashboardPageSubtitle');
    const search = document.getElementById('dashboardSearchInput');

    if (nameEl) nameEl.textContent = userName;
    if (status) status.textContent = `Welcome, ${shortName}!`;
    if (subtitle) subtitle.textContent = `Welcome ${userName}`;
    if (search) search.placeholder = `${shortName}, search farmers products...`;
}

function resolveUserName() {
    const params = new URLSearchParams(window.location.search);
    const queryUser = params.get('user');
    const storedUser = localStorage.getItem('dashboardUserName');
    const fallbackUser = 'Anita Sharma';

    if (queryUser && queryUser.trim()) {
        localStorage.setItem('dashboardUserName', queryUser.trim());
        return queryUser.trim();
    }

    if (storedUser && storedUser.trim()) {
        return storedUser.trim();
    }

    localStorage.setItem('dashboardUserName', fallbackUser);
    return fallbackUser;
}

// Animation Setup
function setupRevealAnimation() {
    const revealTargets = document.querySelectorAll('.top-bar, .hero-card, .stat-card, .content-card');
    revealTargets.forEach((element, index) => {
        element.style.animationDelay = `${index * 60}ms`;
    });
}

// Search Functionality
function setupSearch() {
    const searchInput = document.getElementById('dashboardSearchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        const query = this.value.trim().toLowerCase();
        filterProducts(query);
    });

    filterProducts('');
}

function filterProducts(query) {
    const normalized = query.toLowerCase();
    const products = document.querySelectorAll('.product-card');
    let visibleCount = 0;

    products.forEach(card => {
        const title = card.querySelector('h3')?.textContent.toLowerCase() || '';
        const farmer = card.querySelector('.meta-row')?.textContent.toLowerCase() || '';
        const isVisible = !normalized || title.includes(normalized) || farmer.includes(normalized);

        card.classList.toggle('is-hidden', !isVisible);
        if (isVisible) visibleCount += 1;
    });

    const counter = document.getElementById('productCount');
    if (counter) {
        counter.textContent = visibleCount;
    }
}

// Wishlist Functionality
function setupWishlistActions() {
    const buttons = document.querySelectorAll('.wishlist-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productCard = this.closest('.product-card');
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
    refreshDashboardCounts();
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

// Cart Functionality
function addToCart(productId, productName, price, unit) {
    // This would typically make an AJAX call to add to cart
    // For now, we'll just show a toast
    showToast(`${productName} added to cart`);
    refreshDashboardCounts();
}

// Dashboard Counts
function refreshDashboardCounts() {
    const wishlist = getWishlist();
    const cartCount = 0; // This would come from server
    const messagesCount = 0; // This would come from server

    setText('wishlistBadge', String(wishlist.length));
    setText('cartBadge', String(cartCount));
    setText('messagesBadge', String(messagesCount));
}

// Stats Animation
function animateStats() {
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            const numberEl = card.querySelector('.stat-number');
            if (numberEl) {
                const target = parseInt(numberEl.textContent) || 0;
                animateNumber(numberEl, 0, target, 1000);
            }
        }, index * 200);
    });
}

function animateNumber(element, start, end, duration) {
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Toast Notifications
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

// Utility Functions
function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}