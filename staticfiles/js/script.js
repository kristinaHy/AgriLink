// AgriLink Script

document.addEventListener('DOMContentLoaded', function () {
    // Initialize tooltips and popovers if using Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add scroll animation to cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease-out forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.product-card, .feature-card, .farmer-card').forEach(card => {
        observer.observe(card);
    });

    // Add to cart functionality (placeholder)
    document.querySelectorAll('.btn-add-to-cart').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            // This will be implemented with proper backend integration
            console.log('Added product ' + productId + ' to cart');
        });
    });

    // Search form validation
    const searchForms = document.querySelectorAll('form.search-form, form.search-form-wrapper');
    searchForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const searchInput = this.querySelector('input[name="q"]');
            if (!searchInput) {
                return;
            }
            if (searchInput.value.trim() === '') {
                e.preventDefault();
                searchInput.classList.add('is-invalid');
            }
        });
    });

    // Global search inputs outside forms
    const globalSearchInputs = document.querySelectorAll('.search-bar input[type="text"]');
    globalSearchInputs.forEach(input => {
        input.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter') {
                return;
            }
            const query = this.value.trim();
            e.preventDefault();
            window.location.href = '/search/' + (query ? '?q=' + encodeURIComponent(query) : '');
        });
    });
});

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);
