let isDarkMode = false;

// Function to show error message
function showError(message) {
    const loginError = document.getElementById('loginError');
    const errorSpan = loginError.querySelector('span');
    errorSpan.textContent = message;
    loginError.style.display = 'block';
}

// Function to hide error message
function hideError() {
    const loginError = document.getElementById('loginError');
    loginError.style.display = 'none';
}

// Function to validate form
function validateForm() {
    const emailInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitButton = document.querySelector('.submit-button');
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    // Basic email validation (must contain @ and have at least 5 characters)
    const emailValid = email.length >= 5 && email.includes('@');
    const passwordValid = password.length >= 1;

    if (!emailValid || !passwordValid) {
        submitButton.disabled = true;
        return false;
    } else {
        submitButton.disabled = false;
        return true;
    }
}

// Theme toggle with proper state management
function toggleTheme() {
    isDarkMode = !isDarkMode;
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');

    const themeIcon = document.querySelector('.theme-toggle i');
    themeIcon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';

    // Save preference
    localStorage.setItem('darkMode', isDarkMode);
}

// Hide error when user starts typing
document.getElementById('username').addEventListener('input', function () {
    hideError();
    validateForm();
});

// Hide error when password is entered
document.getElementById('password').addEventListener('input', function () {
    hideError();
    validateForm();
});

// Focus on username input when page loads
document.addEventListener('DOMContentLoaded', function () {
    const usernameInput = document.getElementById('username');
    usernameInput.focus();

    // Load theme preference
    const savedTheme = localStorage.getItem('darkMode');
    if (savedTheme === 'true') {
        isDarkMode = true;
        document.documentElement.setAttribute('data-theme', 'dark');
        const themeIcon = document.querySelector('.theme-toggle i');
        themeIcon.className = 'fas fa-sun';
    }

    // Disclaimer toggle
    const disclaimerToggle = document.querySelector('.disclaimer-toggle');
    if (disclaimerToggle) {
        disclaimerToggle.addEventListener('click', function () {
            this.closest('.disclaimer').classList.toggle('collapsed');
        });
    }

    // Check if user is already logged in
    const storedUsername = sessionStorage.getItem('binat_username');
    const storedUserId = sessionStorage.getItem('binat_user_id');
    const storedPdnCode = sessionStorage.getItem('binat_pdn_code');

    if (storedUsername && storedUserId && storedPdnCode) {
        // User is already logged in, redirect to chat
        window.location.href = `/pdn-binat/binat?user_name=${encodeURIComponent(storedUsername)}&user_id=${encodeURIComponent(storedUserId)}&pdn_code=${encodeURIComponent(storedPdnCode)}`;
        return;
    }

    // Check if we have a stored username for auto-fill
    if (storedUsername) {
        usernameInput.value = storedUsername;
        validateForm();
    }
});

// Form submission
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const emailInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitButton = document.querySelector('.submit-button');
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    if (!email || !password) {
        showError('אנא הזן אימייל וסיסמה');
        return;
    }

    // Show loading state
    submitButton.classList.add('loading');
    submitButton.disabled = true;

    try {
        // Make API call to login endpoint
        const response = await fetch('/pdn-binat/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.success) {
            // Store user data in sessionStorage
            sessionStorage.setItem('binat_username', data.user_name);
            sessionStorage.setItem('binat_user_id', data.user_id);
            sessionStorage.setItem('binat_pdn_code', data.pdn_code);

            // Redirect to chat-ai with user data including PDN code
            window.location.href = `/pdn-binat/binat?user_name=${encodeURIComponent(data.user_name)}&user_id=${encodeURIComponent(data.user_id)}&pdn_code=${encodeURIComponent(data.pdn_code)}`;
        } else {
            showError(data.error || 'שגיאה בהתחברות');
            submitButton.classList.remove('loading');
            submitButton.disabled = false;
        }
    } catch (error) {
        showError('שגיאה בחיבור לשרת');
        submitButton.classList.remove('loading');
        submitButton.disabled = false;
    }
});
