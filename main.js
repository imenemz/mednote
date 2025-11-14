// ===============================================
// ClinicalRoots: FINAL MAIN APPLICATION SCRIPT (main.js)
// 100% compatible with index.html IDs and JWT-based app.py backend.
// ===============================================

// --- GLOBAL STATE ---
let currentUser = null;
let currentCategoryFilter = ''; // The category currently selected (e.g., 'anatomy')
let currentNoteId = null; // The ID of the note currently being viewed/edited
let currentNoteCategory = ''; // The category of the note being viewed/edited

// --- DOM ELEMENT MAPPING (Matched EXACTLY to your index.html IDs) ---
const elements = {
    // Content Views (Pages)
    pages: {
        home: document.getElementById('homePage'),
        library: document.getElementById('libraryPage'),
        noteView: document.getElementById('noteContentPage'),
        admin: document.getElementById('adminDashboardPage'),
        ai: document.getElementById('iaPage'),
        tools: document.getElementById('toolsPage'),
        about: document.getElementById('aboutPage'),
    },

    // Authentication & User Menu
    loginModal: document.getElementById('loginModal'),
    loginForm: document.getElementById('loginForm'),
    userDropdownContent: document.getElementById('userDropdownContent'),
    loginBtn: document.getElementById('loginBtn'),
    userBtn: document.querySelector('.user-btn'),
    userEmailDisplay: document.getElementById('userEmailDisplay'),

    // Library
    subcategoriesGrid: document.getElementById('subcategoriesGrid'),
    categoryNotesList: document.getElementById('categoryNotesList'),
    notesContainer: document.getElementById('notesContainer'),
    notesListHeader: document.getElementById('notesListHeader'),

    // Note View
    noteTitle: document.getElementById('noteTitle'),
    noteTextContent: document.getElementById('noteTextContent'),
    noteViews: document.getElementById('noteViews'),
    noteCategory: document.getElementById('noteCategory'),
    noteEditorSection: document.getElementById('noteEditor'),

    // Note CRUD Modal
    noteCrudModal: document.getElementById('noteCrudModal'),
    noteCrudHeader: document.getElementById('noteCrudHeader'),
    noteCrudForm: document.getElementById('noteCrudForm'),
    noteIdInput: document.getElementById('noteIdInput'),
    noteTitleInput: document.getElementById('noteTitleInput'),
    noteCategorySelect: document.getElementById('noteCategorySelect'),
    noteContentTextarea: document.getElementById('noteContentTextarea'),
    noteCrudSubmitBtn: document.getElementById('noteCrudSubmitBtn'),

    // Admin Dashboard
    adminStats: {
        totalNotes: document.getElementById('totalNotesStat'),
        totalUsers: document.getElementById('totalUsersStat'),
        totalViews: document.getElementById('totalViewsStat'),
        lastUpdate: document.getElementById('lastUpdateStat'),
    },
    adminTopNotesList: document.getElementById('adminTopNotesList'),

    // Search
    searchInput: document.getElementById('searchInput'),
    searchSuggestions: document.getElementById('searchSuggestions'),
};
window.elements = elements;

// ===============================================
// JWT Helper
// ===============================================
function getAuthHeaders() {
    const token = sessionStorage.getItem('jwt');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

async function api(url, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
        ...getAuthHeaders()
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401 || response.status === 422) {
        alert("Session expired. Please log in again.");
        handleLogout(false);
        openLogin();
        throw new Error("Unauthorized");
    }

    if (response.status === 204) return {};

    return response.json();
}

// ===============================================
// View Management
// ===============================================
function switchView(view) {
    Object.values(elements.pages).forEach(p => p.classList.add('hidden'));
    elements.pages[view].classList.remove('hidden');
}

function showHome() {
    switchView('home');
}

function showLibrary() {
    switchView('library');
    elements.subcategoriesGrid.style.display = 'grid';
    elements.categoryNotesList.style.display = 'none';
    fetchAndRenderCategories();
}

function showTools() { switchView('tools'); }
function showIA() { switchView('ai'); }
function showAbout() { switchView('about'); }

function showAdminDashboard() {
    if (currentUser?.role !== 'admin') {
        alert("Access Denied.");
        return;
    }
    switchView('admin');
    fetchAdminStats();
    fetchTopNotes();
}

// ===============================================
// Auth
// ===============================================
function openLogin() { elements.loginModal.style.display = 'flex'; }
function closeLogin() { elements.loginModal.style.display = 'none'; }

async function handleLogin(e) {
    e.preventDefault();

    const email = elements.loginForm.email.value;
    const password = elements.loginForm.password.value;

    const data = await api('/api/login', {
        method: 'POST',
        headers: { "Authorization": "" },
        body: JSON.stringify({ email, password })
    });

    if (!data.token) return alert(data.message);

    sessionStorage.setItem('jwt', data.token);
    sessionStorage.setItem('user', JSON.stringify(data.user));

    currentUser = data.user;
    updateLoginButton();
    closeLogin();

    if (currentUser.role === 'admin') showAdminDashboard();
    else showHome();
}

function handleLogout(showAlert = true) {
    sessionStorage.clear();
    currentUser = null;
    updateLoginButton();
    showHome();
    if (showAlert) alert("Logged out.");
}

function updateLoginButton() {
    const user = sessionStorage.getItem('user');
    currentUser = user ? JSON.parse(user) : null;

    if (!currentUser) {
        elements.loginBtn.style.display = 'inline-block';
        elements.userBtn.style.display = 'none';
        return;
    }

    elements.loginBtn.style.display = 'none';
    elements.userBtn.style.display = 'block';
    elements.userEmailDisplay.textContent = currentUser.email;
}

// ===============================================
// Categories & Notes
// ===============================================
async function fetchAndRenderCategories() {
    let data = await api('/api/categories');
    elements.subcategoriesGrid.innerHTML = '';

    data.forEach(cat => {
        let div = document.createElement('div');
        div.className = 'subcategory-card';
        div.onclick = () => showSubcategory(cat.db_name, cat.name);

        div.innerHTML = `
            <h4>${cat.name}</h4>
            <p>${cat.description}</p>
            <div class="note-count">${cat.notes} notes</div>
        `;

        elements.subcategoriesGrid.appendChild(div);
    });
}

function showSubcategory(db, name) {
    currentCategoryFilter = db;
    elements.subcategoriesGrid.style.display = 'none';
    elements.categoryNotesList.style.display = 'block';
    elements.notesListHeader.textContent = name;
    fetchAndRenderNotes(db);
}

async function fetchAndRenderNotes(category) {
    let notes = await api(`/api/notes?category=${category}`);
    elements.notesContainer.innerHTML = '';

    if (notes.length === 0) {
        elements.notesContainer.innerHTML = `<p>No notes available.</p>`;
        return;
    }

    notes.forEach(note => {
        let item = document.createElement('div');
        item.className = 'note-item';
        item.onclick = () => showNoteView(note.id);

        item.innerHTML = `
            <h4>${note.title}</h4>
            <p class="note-meta">Views: ${note.views}</p>
        `;

        elements.notesContainer.appendChild(item);
    });
}

// ===============================================
// Note View
// ===============================================
async function showNoteView(id) {
    currentNoteId = id;
    switchView('noteView');

    elements.noteTitle.textContent = 'Loading...';

    const note = await api(`/api/note/${id}`);

    elements.noteTitle.textContent = note.title;
    elements.noteTextContent.innerHTML = note.content;
    elements.noteViews.innerHTML = `<i class="fas fa-eye"></i> ${note.views}`;
    elements.noteCategory.textContent = note.category.replace("_"," ").toUpperCase();

    if (currentUser?.role === 'admin') elements.noteEditorSection.style.display = 'flex';
    else elements.noteEditorSection.style.display = 'none';
}

// ===============================================
// Note CRUD (Admin)
// ===============================================
async function openNoteCrud(noteId=null) {
    currentNoteId = noteId;
    elements.noteCrudModal.style.display = 'flex';

    const cats = await api('/api/categories/all');
    elements.noteCategorySelect.innerHTML = cats.map(c => `<option value="${c}">${c}</option>`).join("");

    if (!noteId) {
        elements.noteCrudHeader.textContent = "Add Note";
        elements.noteCrudSubmitBtn.textContent = "Create";
        elements.noteContentTextarea.value = "";
        elements.noteTitleInput.value = "";
        return;
    }

    const note = await api(`/api/note/${noteId}`);
    elements.noteCrudHeader.textContent = "Edit Note";
    elements.noteCrudSubmitBtn.textContent = "Update";

    elements.noteTitleInput.value = note.title;
    elements.noteCategorySelect.value = note.category;
    elements.noteContentTextarea.value = note.content;
}

async function handleNoteCrud(e) {
    e.preventDefault();

    const payload = {
        title: elements.noteTitleInput.value,
        category: elements.noteCategorySelect.value,
        content: elements.noteContentTextarea.value
    };

    if (!currentNoteId) {
        await api('/api/note', {
            method:"POST",
            body: JSON.stringify(payload)
        });
        alert("Note created.");
    } else {
        await api(`/api/note/${currentNoteId}`, {
            method:"PUT",
            body: JSON.stringify(payload)
        });
        alert("Note updated.");
    }

    elements.noteCrudModal.style.display = 'none';
    fetchAndRenderNotes(currentCategoryFilter);
}

async function deleteNote() {
    if (!confirm("Delete this note?")) return;
    await api(`/api/note/${currentNoteId}`, { method:"DELETE" });
    alert("Deleted.");
    showLibrary();
}

// ===============================================
// Admin Dashboard
// ===============================================
async function fetchAdminStats() {
    let data = await api('/api/admin_stats');
    data = data.stats;

    elements.adminStats.totalNotes.textContent = data.total_notes;
    elements.adminStats.totalUsers.textContent = data.total_users;
    elements.adminStats.totalViews.textContent = data.total_views;
    elements.adminStats.lastUpdate.textContent = data.last_update ?
        new Date(data.last_update).toLocaleDateString() : "N/A";
}

async function fetchTopNotes() {
    const notes = await api('/api/note_views');
    elements.adminTopNotesList.innerHTML = '';
    notes.forEach(n=>{
        elements.adminTopNotesList.innerHTML += `<p>${n.title} (${n.views})</p>`;
    });
}

// ===============================================
// Search
// ===============================================
async function handleSearch(query) {
    if (query.length < 2) {
        elements.searchSuggestions.innerHTML = "";
        return;
    }

    const results = await api(`/api/notes?search=${encodeURIComponent(query)}`);
    elements.searchSuggestions.innerHTML = "";

    results.slice(0,6).forEach(item=>{
        let div = document.createElement('div');
        div.className = "suggestion-item";
        div.onclick = () => showNoteView(item.id);
        div.innerHTML = `<strong>${item.title}</strong>`;
        elements.searchSuggestions.appendChild(div);
    });
}

// ===============================================
// Initialization
// ===============================================
document.addEventListener('DOMContentLoaded', () => {
    updateLoginButton();

    elements.loginForm.onsubmit = handleLogin;
    elements.noteCrudForm.onsubmit = handleNoteCrud;
    elements.searchInput.oninput = e => handleSearch(e.target.value);

    showHome();
});
