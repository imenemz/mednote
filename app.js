// Application State
let currentUser = null;
let currentTheme = 'dark';

// --- REMOVE: The hardcoded ADMIN_CREDENTIALS object is now gone! ---

// DOM Elements (The element object remains the same)
const elements = {
    // ... all your existing DOM selectors ...
    loginBtn: document.getElementById('loginBtn'),
    // ...
    loginForm: document.getElementById('loginForm'),
    // ...
};

// --- CORE UTILITY FUNCTIONS ---

function updateAuthButtons() {
    // Retrieve user from session storage
    const storedUser = sessionStorage.getItem('user');
    currentUser = storedUser ? JSON.parse(storedUser) : null;

    if (currentUser) {
        // Logged In State
        elements.loginBtn.style.display = 'none';
        elements.registerBtn.style.display = 'none';
        // Show user menu/dropdown
        const userMenu = document.querySelector('.user-menu');
        if (userMenu) userMenu.style.display = 'block';
        
        // Update user display text
        const userEmailDisplay = document.getElementById('userEmailDisplay');
        if (userEmailDisplay) userEmailDisplay.textContent = currentUser.email;

        // Admin Specific UI
        if (currentUser.role === 'admin') {
            document.body.classList.add('admin-logged-in');
            // Re-run the live edit setup for content cards
            setupAdminLiveEdit(); 
        } else {
             document.body.classList.remove('admin-logged-in');
        }
    } else {
        // Logged Out State
        elements.loginBtn.style.display = 'inline-block';
        elements.registerBtn.style.display = 'inline-block';
        const userMenu = document.querySelector('.user-menu');
        if (userMenu) userMenu.style.display = 'none';
        document.body.classList.remove('admin-logged-in');
        
        // Remove contentEditable attributes
        document.querySelectorAll('[data-editable]').forEach(el => {
            el.removeAttribute('contenteditable');
            el.classList.remove('admin-editable-active');
        });
    }
}

// --- NEW API LOGIN FUNCTION ---
async function handleLogin(e) {
    e.preventDefault();
    const email = elements.loginForm.email.value;
    const password = elements.loginForm.password.value;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (data.success) {
            // CRUCIAL: Save user info to sessionStorage
            sessionStorage.setItem('user', JSON.stringify({ email: data.email, role: data.role }));
            currentUser = { email: data.email, role: data.role };
            
            updateAuthButtons();
            closeLoginModal();
            
            if (currentUser.role === 'admin') {
                window.location.href = '/admin'; // Redirect admin to dashboard
            } else {
                alert('Login successful! Welcome.');
            }
        } else {
            alert(data.message || 'Login failed.');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('An error occurred during login. Please try again.');
    }
}
// Assign this new function to the form submit event listener in setupEventListeners()

// --- NEW/UPDATED FETCH NOTES FUNCTION ---
async function fetchAndRenderNotes(category) {
    // The endpoint now returns category along with the note, which is useful for PUT requests.
    const noteContainer = document.getElementById('noteContainer');
    noteContainer.innerHTML = '<div class="loading-message">Loading notes...</div>';

    try {
        const response = await fetch(`/api/notes/${category}`);
        const notes = await response.json();

        noteContainer.innerHTML = '';
        if (notes.length === 0) {
            noteContainer.innerHTML = '<div class="empty-message">No notes found for this category.</div>';
            return;
        }

        notes.forEach(note => {
            const card = document.createElement('div');
            // CRUCIAL: Add data-note-id and data-category for admin editing
            card.className = 'concept-card';
            card.setAttribute('data-note-id', note.id);
            card.setAttribute('data-category', note.category); 
            
            card.innerHTML = `
                <h3 class="concept-title" data-editable>${note.title}</h3>
                <div class="concept-content" data-editable>${note.content}</div>
                <div class="card-footer">
                    <span>Views: ${note.views}</span>
                    <span>Created: ${new Date(note.created_at).toLocaleDateString()}</span>
                </div>
            `;
            noteContainer.appendChild(card);
        });

        // Re-run setupAdminLiveEdit after new cards are rendered
        if (currentUser && currentUser.role === 'admin') {
            setupAdminLiveEdit();
        }

    } catch (error) {
        console.error('Error fetching notes:', error);
        noteContainer.innerHTML = '<div class="error-message">Failed to load content.</div>';
    }
}

// --- NEW ADMIN LIVE EDIT LOGIC ---

// Function to handle saving the note via API
function saveNoteUpdate(noteId, payload, element) {
    fetch(`/api/notes/${noteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to save update.');
        }
        // Visual feedback (Success)
        element.style.transition = 'background-color 0.5s';
        element.style.backgroundColor = 'rgba(25, 62, 55, 0.2)'; 
        setTimeout(() => { element.style.backgroundColor = ''; }, 800);
        return response.json();
    })
    .catch(error => {
        console.error('Save failed:', error);
        alert('Failed to save changes: ' + error.message);
        // Visual feedback (Error)
        element.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
    });
}

// Function to enable in-place editing for the admin
function setupAdminLiveEdit() {
    const user = currentUser; // Use the global currentUser state
    
    // Only run if the user is an admin
    if (!user || user.role !== 'admin') {
        return; 
    }
    
    document.querySelectorAll('[data-editable]').forEach(element => {
        // 1. Enable editing
        element.setAttribute('contenteditable', 'true');
        element.classList.add('admin-editable-active'); 
        
        // 2. Add listener to SAVE when the element loses focus
        element.addEventListener('blur', function() {
            const card = this.closest('.concept-card');
            const noteId = card?.dataset.noteId;
            const category = card?.dataset.category;

            if (!noteId || !category) return;
            
            // Collect the edited data from the card elements
            const newTitle = card.querySelector('.concept-title')?.textContent.trim() || '';
            const newContent = card.querySelector('.concept-content')?.innerHTML.trim() || ''; // Use innerHTML for rich text
            
            const payload = {
                title: newTitle,
                content: newContent,
                category: category,
                is_published: 1 
            };
            
            saveNoteUpdate(noteId, payload, this);
        });
    });
}

// --- INITIALIZATION ---

function setupEventListeners() {
    // ... (existing event listeners) ...

    // NEW: Register button opens the modal
    if (elements.registerBtn) {
        elements.registerBtn.addEventListener('click', showSignup);
    }

    // NEW: Close register modal button
    if (elements.closeRegisterModal) {
        elements.closeRegisterModal.addEventListener('click', closeSignup);
    }

    // NEW: Register form submission
    if (elements.registerForm) {
        elements.registerForm.addEventListener('submit', handleRegister);
    }

    // NEW: Live password match check for visual feedback
    const registerPasswordInput = document.getElementById('registerPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');

    if (registerPasswordInput && confirmPasswordInput) {
        const checkPasswordMatch = () => {
            if (registerPasswordInput.value === confirmPasswordInput.value) {
                elements.passwordMatchError.style.display = 'none';
                confirmPasswordInput.style.borderColor = ''; // Reset border
            } else {
                elements.passwordMatchError.style.display = 'block';
                // You can add a red border here using CSS variables if you want more visual feedback
            }
        };
        registerPasswordInput.addEventListener('input', checkPasswordMatch);
        confirmPasswordInput.addEventListener('input', checkPasswordMatch);
    }

    // ... (rest of setupEventListeners) ...
}


// Initialize Application
function init() {
    // This order is important
    updateAuthButtons(); // Sets currentUser and checks for admin status
    setupEventListeners();
    initializeTheme();
    setupSmoothScrolling();
    setupCardInteractions();
    setupFormValidation(); 
    setupAdminLiveEdit(); // Runs only if updateAuthButtons sets role as admin
    
    // Ensure the default category is fetched on load
    fetchAndRenderNotes('anatomy');

    console.log('MedMaster application initialized');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
