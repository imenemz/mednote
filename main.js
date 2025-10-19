// MedMaster - Medical Education Platform JavaScript - Updated

class MedMasterApp {
    constructor() {
        this.currentTheme = localStorage.getItem('medmaster_theme') || 'dark';
        this.isAdmin = false;
        this.adminCredentials = {
            email: 'imenemazouz05@gmail.com',
            password: 'Zain%2005'
        };
        this.init();
    }

    init() {
        this.setTheme(this.currentTheme);
        this.setupEventListeners();
        this.checkAdminStatus();
        this.initializeAnimations();
    }

    setupEventListeners() {
        // Close theme menu when clicking outside
        document.addEventListener('click', (e) => {
            const themeMenu = document.getElementById('themeMenu');
            const themeToggle = document.querySelector('.theme-toggle');

            if (!themeMenu.contains(e.target) && !themeToggle.contains(e.target)) {
                themeMenu.classList.remove('active');
            }
        });

        // Smooth scroll for navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                if (link.getAttribute('href').startsWith('#')) {
                    e.preventDefault();
                    const targetId = link.getAttribute('href');
                    this.scrollToSection(targetId);
                }
            });
        });
    }

    checkAdminStatus() {
        // Check if user is admin with new credentials
        const userEmail = sessionStorage.getItem('user_email');
        if (userEmail === this.adminCredentials.email) {
            this.isAdmin = true;
            document.body.classList.add('admin');
            this.showViewCounts();
            this.displayAdminEmail();
        }
    }

    displayAdminEmail() {
        // Show admin email in dashboard
        const adminEmailElements = document.querySelectorAll('.admin-email');
        adminEmailElements.forEach(element => {
            element.textContent = this.adminCredentials.email;
        });
    }

    showViewCounts() {
        // Only visible to admin - show view counts
        if (this.isAdmin) {
            // Add view count elements
            const viewCountHTML = '<div class="view-count admin-only">Views: 1,247</div>';

            document.querySelectorAll('.course-card, .tool-card').forEach(card => {
                if (!card.querySelector('.view-count')) {
                    card.innerHTML += viewCountHTML;
                }
            });
        }
    }

    scrollToSection(targetId) {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            const offsetTop = targetElement.offsetTop - 70; // Account for fixed navbar
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    }

    initializeAnimations() {
        // Fade in animation for cards
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe cards for animation
        document.querySelectorAll('.course-card, .tool-card').forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            card.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
            observer.observe(card);
        });
    }
}

// Theme Management Functions
function toggleThemeMenu() {
    const themeMenu = document.getElementById('themeMenu');
    themeMenu.classList.toggle('active');
}

function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('medmaster_theme', theme);

    // Close theme menu
    const themeMenu = document.getElementById('themeMenu');
    if (themeMenu) {
        themeMenu.classList.remove('active');
    }

    // Update stethoscope color based on theme
    const stethoscope = document.querySelector('.theme-toggle i');
    if (stethoscope) {
        stethoscope.style.color = theme === 'dark' ? '#6aa157' : '#4a7c59';
    }

    console.log(`Theme changed to: ${theme}`);
}

// Login simulation function
function simulateLogin(email, password) {
    const app = window.medMasterApp;
    if (email === app.adminCredentials.email && password === app.adminCredentials.password) {
        sessionStorage.setItem('user_email', email);
        sessionStorage.setItem('user_role', 'admin');
        alert('Login successful! Welcome to MedMaster Admin Dashboard.');
        app.checkAdminStatus();
        return true;
    } else {
        alert('Invalid credentials. Please check your email and password.');
        return false;
    }
}

// Password change validation
function validatePasswordChange(currentPassword, newPassword, confirmPassword) {
    const app = window.medMasterApp;

    if (currentPassword !== app.adminCredentials.password) {
        alert('Current password is incorrect.');
        return false;
    }

    if (newPassword.length < 6) {
        alert('New password must be at least 6 characters long.');
        return false;
    }

    if (newPassword !== confirmPassword) {
        alert('New passwords do not match.');
        return false;
    }

    // Simulate password change
    app.adminCredentials.password = newPassword;
    alert('Password changed successfully!');
    return true;
}

// Course loading function
function loadCourseNotes(category) {
    const courseInfo = {
        'anatomy': {
            name: 'Anatomy',
            topics: ['Human Heart Structure', 'Skeletal System', 'Nervous System Basics'],
            count: 3
        },
        'physiology': {
            name: 'Physiology', 
            topics: ['Cardiac Cycle', 'Respiratory Function'],
            count: 2
        },
        'pathology': {
            name: 'Pathology',
            topics: ['Myocardial Infarction', 'Pneumonia'], 
            count: 2
        }
    };

    const course = courseInfo[category];
    if (course) {
        let topicsList = course.topics.map(topic => `• ${topic}`).join('\n');
        alert(`${course.name} Course\n\n${course.count} topics available:\n\n${topicsList}\n\n(Click to view detailed content)`);
    }
}

// Scroll to section function
function scrollToSection(sectionId) {
    const target = document.querySelector(sectionId);
    if (target) {
        const offsetTop = target.offsetTop - 70;
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

// Initialize app when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', function() {
    app = new MedMasterApp();
    window.medMasterApp = app;

    console.log('MedMaster application initialized successfully!');
    console.log('New Admin Credentials:');
    console.log('Email: imenemazouz05@gmail.com');
    console.log('Password: Zain%2005');
});