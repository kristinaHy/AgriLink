document.addEventListener('DOMContentLoaded', function() {
    const priceRange = document.getElementById('priceRange');
    const minPrice = document.getElementById('minPrice');
    const maxPrice = document.getElementById('maxPrice');
    const districtCheckboxes = document.querySelectorAll('input[type=\"checkbox\"][value]');
    const sortSelect = document.getElementById('sortSelect');
    const productGrid = document.getElementById('productGrid');
    let products = Array.from(productGrid.querySelectorAll('.product'));
    
    // Update price labels
    function updatePriceLabels() {
        const min = parseInt(priceRange.min, 10);
        const max = parseInt(priceRange.max, 10);
        const value = parseInt(priceRange.value, 10);
        minPrice.textContent = `Rs. ${min}`;
        maxPrice.textContent = `Rs. ${max}`;
    }
    updatePriceLabels();
    
    // Price filter
    priceRange.addEventListener('input', function() {
        const maxPriceVal = parseInt(this.value, 10);
        products.forEach(product => {
            const price = parseFloat(product.dataset.price) || 0;
            product.style.display = price <= maxPriceVal ? '' : 'none';
        });
        updatePriceLabels();
    });
    
    // District filter
    districtCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const selectedDistricts = Array.from(districtCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            
            products.forEach(product => {
                const district = product.dataset.district || '';
                const show = selectedDistricts.length === 0 || selectedDistricts.includes(district);
                product.style.display = show ? '' : 'none';
            });
        });
    });
    
    // Sort products
    sortSelect.addEventListener('change', function() {
        const sortBy = this.value;
        products.sort((a, b) => {
            switch (sortBy) {
                case 'latest':
                    // Assume newer products have higher data-id or add data-timestamp later
                    return parseInt(b.dataset.id || 0) - parseInt(a.dataset.id || 0);
                case 'price-low':
                    return parseFloat(a.dataset.price || 0) - parseFloat(b.dataset.price || 0);
                case 'price-high':
                    return parseFloat(b.dataset.price || 0) - parseFloat(a.dataset.price || 0);
                default:
                    return 0;
            }
        });
        
        // Re-append sorted products
        products.forEach(product => productGrid.appendChild(product));
    });
    
    // Initial sort
    sortSelect.dispatchEvent(new Event('change'));
});
