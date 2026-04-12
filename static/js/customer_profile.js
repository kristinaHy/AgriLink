// Customer Profile JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeUserView();
    setupSidebarActivation();
    setupPreferenceHandlers();
});

function initializeUserView() {
    const userName = localStorage.getItem('dashboardUserName') || 'Anita Sharma';
    const nameEl = document.getElementById('dashboardUsername');
    if (nameEl) nameEl.textContent = userName;
}

function setupSidebarActivation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.href && item.href.includes('profile')) {
            item.classList.add('active');
        }
    });
}

function setupPreferenceHandlers() {
    const checkboxes = document.querySelectorAll('.preferences input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            savePreference(this.id, this.checked);
        });
    });

    // Load saved preferences
    loadPreferences();
}

function savePreference(preferenceId, value) {
    const preferences = getPreferences();
    preferences[preferenceId] = value;
    localStorage.setItem('dashboardPreferences', JSON.stringify(preferences));
    showToast(`Preference ${value ? 'enabled' : 'disabled'}`);
}

function getPreferences() {
    const raw = localStorage.getItem('dashboardPreferences');
    if (!raw) return {};

    try {
        return JSON.parse(raw);
    } catch (error) {
        console.error('Error parsing preferences:', error);
        return {};
    }
}

function loadPreferences() {
    const preferences = getPreferences();
    Object.keys(preferences).forEach(key => {
        const checkbox = document.getElementById(key);
        if (checkbox) {
            checkbox.checked = preferences[key];
        }
    });
}

function editProfile() {
    // This would open an edit profile modal
    showToast('Opening profile editor...');
}

function changePassword() {
    // This would open a change password modal
    showToast('Opening password change form...');
}

function enable2FA() {
    // This would open 2FA setup
    showToast('Opening 2FA setup...');
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