// Application State
let currentUser = null;
let currentTheme = 'dark';

// Admin Credentials
const ADMIN_CREDENTIALS = {
    email: 'imenemazouz05@gmail.com',
    password: 'Zain%2005'
};

// DOM Elements
const elements = {
    // Buttons
    loginBtn: document.getElementById('loginBtn'),
    registerBtn: document.getElementById('registerBtn'),
    themeToggle: document.getElementById('themeToggle'),
    changePasswordBtn: document.getElementById('changePasswordBtn'),
    logoutBtn: document.getElementById('logoutBtn'),
    
    // Modals
    loginModal: document.getElementById('loginModal'),
    registerModal: document.getElementById('registerModal'),
    adminDashboard: document.getElementById('adminDashboard'),
    changePasswordModal: document.getElementById('changePasswordModal'),
    themeModal: document.getElementById('themeModal'),
    
    // Close buttons
    closeLoginModal: document.getElementById('closeLoginModal'),
    closeRegisterModal: document.getElementById('closeRegisterModal'),
    closeAdminDashboard: document.getElementById('closeAdminDashboard'),
    closeChangePasswordModal: document.getElementById('closeChangePasswordModal'),
    closeThemeModal: document.getElementById('closeThemeModal'),
    
    // Forms
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    changePasswordForm: document.getElementById('changePasswordForm'),
    
    // Messages
    passwordError: document.getElementById('passwordError'),
    passwordSuccess: document.getElementById('passwordSuccess'),
    
    // Other elements
    adminEmail: document.getElementById('adminEmail')
};

// Utility Functions
function showModal(modal) {
    modal.classList.remove('hidden');
    // Focus the modal for accessibility
    const firstInput = modal.querySelector('input, button');
    if (firstInput) firstInput.focus();
}

function hideModal(modal) {
    modal.classList.add('hidden');
}

function showMessage(element, message, isError = true) {
    element.textContent = message;
    element.classList.remove('hidden');
    setTimeout(() => {
        element.classList.add('hidden');
    }, 5000);
}

function validatePassword(password) {
    if (password.length < 6) {
        return 'Password must be at least 6 characters long';
    }
    return null;
}

function updateAuthButtons() {
    if (currentUser) {
        elements.loginBtn.textContent = 'Dashboard';
        elements.registerBtn.style.display = 'none';
    } else {
        elements.loginBtn.textContent = 'Login';
        elements.registerBtn.style.display = 'inline-flex';
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // Login button
    elements.loginBtn.addEventListener('click', () => {
        if (currentUser) {
            showModal(elements.adminDashboard);
        } else {
            showModal(elements.loginModal);
        }
    });

    // Register button
    elements.registerBtn.addEventListener('click', () => {
        showModal(elements.registerModal);
    });

    // Theme toggle
    elements.themeToggle.addEventListener('click', () => {
        showModal(elements.themeModal);
    });

    // Change password button
    elements.changePasswordBtn.addEventListener('click', () => {
        hideModal(elements.adminDashboard);
        showModal(elements.changePasswordModal);
    });

    // Logout button
    elements.logoutBtn.addEventListener('click', () => {
        currentUser = null;
        updateAuthButtons();
        hideModal(elements.adminDashboard);
        alert('Logged out successfully!');
    });

    // Close modal buttons
    elements.closeLoginModal.addEventListener('click', () => {
        hideModal(elements.loginModal);
    });

    elements.closeRegisterModal.addEventListener('click', () => {
        hideModal(elements.registerModal);
    });

    elements.closeAdminDashboard.addEventListener('click', () => {
        hideModal(elements.adminDashboard);
    });

    elements.closeChangePasswordModal.addEventListener('click', () => {
        hideModal(elements.changePasswordModal);
    });

    elements.closeThemeModal.addEventListener('click', () => {
        hideModal(elements.themeModal);
    });

    // Click outside modal to close
    [elements.loginModal, elements.registerModal, elements.adminDashboard, 
     elements.changePasswordModal, elements.themeModal].forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal(modal);
            }
        });
    });

    // Form submissions
    elements.loginForm.addEventListener('submit', handleLogin);
    elements.registerForm.addEventListener('submit', handleRegister);
    elements.changePasswordForm.addEventListener('submit', handlePasswordChange);

    // Theme options
    document.querySelectorAll('.theme-option').forEach(option => {
        option.addEventListener('click', (e) => {
            const theme = e.target.getAttribute('data-theme');
            setTheme(theme);
            hideModal(elements.themeModal);
        });
    });

    // Escape key to close modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            [elements.loginModal, elements.registerModal, elements.adminDashboard, 
             elements.changePasswordModal, elements.themeModal].forEach(modal => {
                if (!modal.classList.contains('hidden')) {
                    hideModal(modal);
                }
            });
        }
    });
}

// Authentication Functions
function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    
    // Check admin credentials
    if (email === ADMIN_CREDENTIALS.email && password === ADMIN_CREDENTIALS.password) {
        currentUser = {
            email: email,
            type: 'admin'
        };
        
        updateAuthButtons();
        hideModal(elements.loginModal);
        alert('Login successful! Welcome, Admin.');
        
        // Clear form
        elements.loginForm.reset();
    } else {
        alert('Invalid credentials. Please try again.');
    }
}

function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    
    // Basic validation
    if (!name || !email || !password) {
        alert('Please fill in all fields.');
        return;
    }
    
    const passwordError = validatePassword(password);
    if (passwordError) {
        alert(passwordError);
        return;
    }
    
    // Simulate registration
    alert('Registration successful! You can now login.');
    hideModal(elements.registerModal);
    
    // Clear form
    elements.registerForm.reset();
}

function handlePasswordChange(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Clear previous messages
    elements.passwordError.classList.add('hidden');
    elements.passwordSuccess.classList.add('hidden');
    
    // Validate current password
    if (currentPassword !== ADMIN_CREDENTIALS.password) {
        showMessage(elements.passwordError, 'Current password is incorrect.');
        return;
    }
    
    // Validate new password
    const passwordError = validatePassword(newPassword);
    if (passwordError) {
        showMessage(elements.passwordError, passwordError);
        return;
    }
    
    // Check if passwords match
    if (newPassword !== confirmPassword) {
        showMessage(elements.passwordError, 'New passwords do not match.');
        return;
    }
    
    // Check if new password is different from current
    if (newPassword === currentPassword) {
        showMessage(elements.passwordError, 'New password must be different from current password.');
        return;
    }
    
    // Update password (in real app, this would be sent to server)
    ADMIN_CREDENTIALS.password = newPassword;
    
    showMessage(elements.passwordSuccess, 'Password updated successfully!', false);
    
    // Clear form after delay
    setTimeout(() => {
        elements.changePasswordForm.reset();
        hideModal(elements.changePasswordModal);
    }, 2000);
}

// Theme Functions
function setTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-color-scheme', theme);
    
    // Update theme toggle icon
    elements.themeToggle.textContent = theme === 'dark' ? '🩺' : '🩺';
    elements.themeToggle.title = `Current theme: ${theme}. Click to change.`;
}

function initializeTheme() {
    // Start with dark theme as requested
    setTheme('dark');
}

// Smooth scrolling for navigation links
function setupSmoothScrolling() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Course and tool card interactions
function setupCardInteractions() {
    document.querySelectorAll('.course-card, .tool-card').forEach(card => {
        card.addEventListener('click', () => {
            const title = card.querySelector('h3').textContent;
            alert(`${title} - Coming soon! Full content will be available in the complete version.`);
        });
        
        // Add keyboard navigation
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'button');
        
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });
    });
}

// Form validation enhancements
function setupFormValidation() {
    // Real-time password strength indicator for change password form
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    
    if (newPasswordInput) {
        newPasswordInput.addEventListener('input', (e) => {
            const password = e.target.value;
            const helpText = newPasswordInput.parentNode.querySelector('.form-help');
            
            if (password.length === 0) {
                helpText.textContent = 'Password must be at least 6 characters long';
                helpText.style.color = 'var(--color-text-secondary)';
            } else if (password.length < 6) {
                helpText.textContent = `${6 - password.length} more characters needed`;
                helpText.style.color = 'var(--color-warning)';
            } else {
                helpText.textContent = 'Password strength: Good';
                helpText.style.color = 'var(--color-success)';
            }
        });
    }
    
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', (e) => {
            const newPassword = newPasswordInput.value;
            const confirmPassword = e.target.value;
            
            if (confirmPassword.length > 0) {
                if (newPassword === confirmPassword) {
                    confirmPasswordInput.style.borderColor = 'var(--color-success)';
                } else {
                    confirmPasswordInput.style.borderColor = 'var(--color-error)';
                }
            } else {
                confirmPasswordInput.style.borderColor = 'var(--color-border)';
            }
        });
    }
}

// Initialize Application
function init() {
    setupEventListeners();
    initializeTheme();
    setupSmoothScrolling();
    setupCardInteractions();
    setupFormValidation();
    updateAuthButtons();
    
    console.log('MedMaster application initialized');
    console.log('Admin credentials: imenemazouz05@gmail.com / Zain%2005');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);