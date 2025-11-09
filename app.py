from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import secrets
import time # For __diag route

# --- CRITICAL DEPLOYMENT PATH CORRECTION (FIX 6) ---
# Define the base directory of the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'medmaster.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads') # Use absolute path for safety

# Ensure directories exist
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app = Flask(__name__,
            # Configure Flask to look for static files (app.js, style.css) in the 'frontend' folder
            static_folder=os.path.join(BASE_DIR, 'frontend'),
            # Configure Flask to look for templates (index.html) in the 'frontend' folder
            template_folder=os.path.join(BASE_DIR, 'frontend'))

# FIX 6: Use environment variable for SECRET_KEY (best practice for production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


# --- Database Connection and Initialization Functions ---

def get_db_connection():
    # Use the absolute path for persistent connection
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Create Users Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    # 2. Create Medical Notes Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL, -- NOTE: This is the subcategory (e.g., 'anatomy')
            content TEXT NOT NULL,
            author_id INTEGER,
            views INTEGER DEFAULT 0,
            is_published BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    """)

    # 3. Check for and Create Default Admin User & Sample Data
    c.execute("SELECT * FROM users WHERE email = 'imenemazouz05@gmail.com'")
    if c.fetchone() is None:
        # Admin Login: imenemazouz05@gmail.com / Zain%2005
        admin_password_hash = generate_password_hash('Zain%2005')
        c.execute("INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                  ('admin_user', 'imenemazouz05@gmail.com', admin_password_hash, 'admin'))

        # Insert sample data (Admin ID is 1 if it's the first user)
        sample_notes = [
            # Medical Subcategories
            ('Human Heart Structure', 'anatomy', '<h3>Overview</h3><p>The human heart is a muscular organ with four chambers.</p>'),
            ('Skeletal System', 'anatomy', '<h3>Overview</h3><p>The skeletal system provides structural support.</p>'),
            ('Nervous System Basics', 'anatomy', '<h3>Overview</h3><p>Central and peripheral nervous systems control body functions.</p>'),
            ('Cardiac Cycle', 'physiology', '<h3>Systole and Diastole</h3><p>Heart contraction and relaxation phases.</p>'),
            ('Respiratory Function', 'physiology', '<h3>Gas Exchange</h3><p>Oxygen and carbon dioxide exchange in lungs.</p>'),
            ('Myocardial Infarction', 'pathology', '<h3>Heart Attack</h3><p>Death of heart muscle due to blocked blood supply.</p>'),
            ('Pneumonia', 'pathology', '<h3>Lung Infection</h3><p>Bacterial or viral infection of lung tissue.</p>'),
            # Specialty Subcategories
            ('Acute Coronary Syndrome', 'cardiology', '<h3>Overview</h3><p>A set of conditions associated with sudden reduced blood flow to the heart.</p>'),
            ('Parkinsons Disease', 'neurology', '<h3>Overview</h3><p>A progressive nervous system disorder affecting movement.</p>'),
            # Surgical Subcategories
            ('Appendectomy Procedure', 'general_surgery', '<h3>Overview</h3><p>Surgical removal of the appendix.</p>'),
        ]

        # Note: We assume the admin_user is id=1, which is safe on first run
        for note in sample_notes:
            c.execute('INSERT INTO medical_notes (title, category, content, author_id) VALUES (?, ?, ?, 1)', note)
        print("Default admin user and sample data created.")

    conn.commit()
    conn.close()

# --- FIX 4: Ensure DB init runs on WSGI startup ---
@app.before_first_request
def boot():
    """Initializes the database before the first request in a WSGI environment."""
    try:
        init_db()
    except Exception as e:
        # This will show up in the PythonAnywhere error log
        print(f"Startup database initialization error: {e}") 

# --- FIX 3: Add an anti-cache header for HTML ---
@app.after_request
def no_cache_for_html(resp):
    """Prevents browsers/Nginx from caching HTML files while debugging."""
    if resp.mimetype == 'text/html':
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
    return resp

# --- FIX 5: Diagnostics Route (Debug Only) ---
@app.route('/__diag')
def __diag():
    """Returns diagnostic information about the running environment."""
    idx = os.path.join(BASE_DIR, 'frontend', 'index.html')
    # Assumes your JavaScript file has been renamed to app.js
    js  = os.path.join(BASE_DIR, 'frontend', 'app.js') 
    
    info = {
        "py_file": __file__,
        "db_path": DB_PATH,
        "index_exists": os.path.exists(idx),
        "index_mtime": time.ctime(os.path.getmtime(idx)) if os.path.exists(idx) else "N/A",
        "js_filename_check": "app.js",
        "js_exists": os.path.exists(js),
        "js_mtime": time.ctime(os.path.getmtime(js)) if os.path.exists(js) else "N/A (Ensure app (2).js is renamed to app.js)",
        "session_role": session.get('role'),
    }
    return jsonify(info)


# --- Flask Routes ---

@app.route('/')
def index():
    # Renders the main HTML file (frontend/index.html)
    return render_template('index.html')

# --- USER & SESSION ROUTES ---

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['logged_in'] = True
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['role'] = user['role']
        return jsonify({'success': True, 'email': user['email'], 'role': user['role'], 'user_id': user['id']})
    
    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/change_password', methods=['POST'])
def change_password():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Please login to change your password'}), 401

    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()

    if not user or not check_password_hash(user['password_hash'], current_password):
        conn.close()
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

    new_password_hash = generate_password_hash(new_password)
    try:
        conn.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                     (new_password_hash, session['user_id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Password changed successfully!'})
    except Exception as e:
        print(f"Error updating password: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during password change.'}), 500
    finally:
        conn.close()

# --- DYNAMIC CATEGORY ROUTE (Fulfills the request for dynamic subcategories) ---
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    # Get unique subcategories (which is the 'category' column) and count notes in each
    query = """
        SELECT category, COUNT(id) as note_count
        FROM medical_notes
        WHERE is_published = 1
        GROUP BY category
        ORDER BY category
    """
    categories = conn.execute(query).fetchall()
    conn.close()

    # Determine the 'major' category and assign display info
    def get_major_category_info(subcat_db_name):
        subcat_db_name = subcat_db_name.lower()

        # Hardcoded mapping to major categories and display descriptions
        mapping = {
            'anatomy': ('Medical', 'Structure and organization of the human body'),
            'physiology': ('Medical', 'Function of the human body systems'),
            'pathology': ('Medical', 'Study of disease'),
            'pharmacology': ('Medical', 'Drug actions and effects'),
            'general_surgery': ('Surgical', 'Common surgical procedures'),
            'orthopedics': ('Surgical', 'Musculoskeletal system surgery'),
            'neurosurgery': ('Surgical', 'Nervous system surgery'),
            'cardiology': ('Specialty', 'Heart and vascular diseases'),
            'neurology': ('Specialty', 'Nervous system disorders'),
            'endocrinology': ('Specialty', 'Hormonal disorders'),
        }
        # Fallback for dynamic/new categories created by admin
        return mapping.get(subcat_db_name, ('Other', 'In-depth concepts and clinical notes.'))


    structured_data = {
        'Medical': [],
        'Surgical': [],
        'Specialty': [],
    }

    for row in categories:
        subcat_db_name = row['category']
        note_count = row['note_count']
        major_cat, description = get_major_category_info(subcat_db_name)

        if major_cat in structured_data:
            display_name = subcat_db_name.replace('_', ' ').title()

            structured_data[major_cat].append({
                'name': display_name,
                'db_name': subcat_db_name, # Critical for API calls
                'notes': note_count,
                'description': description,
            })
        # Ignore 'Other' for the main navigation view for simplicity, or handle it here if needed

    return jsonify(structured_data)

# --- NOTES RETRIEVAL ROUTES (Used by both user and admin) ---

@app.route('/api/notes', methods=['GET'])
def get_notes():
    conn = get_db_connection()
    category = request.args.get('category')
    search_query = request.args.get('search')
    
    query = "SELECT id, title, category, content, views, created_at FROM medical_notes WHERE is_published = 1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)
    
    if search_query:
        # Simple LIKE search on title and content
        query += " AND (title LIKE ? OR content LIKE ?)"
        # Note: Added % for wildcard matching for search
        params.append(f'%{search_query}%') 
        params.append(f'%{search_query}%')

    query += " ORDER BY created_at DESC"

    notes = conn.execute(query, params).fetchall()
    conn.close()
    
    # Return as a list of dictionaries
    return jsonify([dict(note) for note in notes])

@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_single_note(note_id):
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, category, content, views FROM medical_notes WHERE id = ? AND is_published = 1", (note_id,)).fetchone()
    
    if note is None:
        conn.close()
        return jsonify({'success': False, 'message': 'Note not found or not published.'}), 404

    # Increment view count
    conn.execute('UPDATE medical_notes SET views = views + 1 WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'note': dict(note)})

# --- ADMIN NOTES CRUD ROUTES (Fulfills the request for admin actions stored in DB) ---

@app.route('/api/notes', methods=['POST'])
def add_note():
    # Authorization check
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin privileges required to add notes.'}), 403

    data = request.get_json()
    title = data.get('title')
    category = data.get('category') # Expected to be the subcategory (e.g., 'anatomy')
    content = data.get('content')
    author_id = session.get('user_id')

    if not title or not category or not content:
        return jsonify({'success': False, 'message': 'Title, category, and content are required.'}), 400

    conn = get_db_connection()
    try:
        # Notes are now stored in the database
        conn.execute('INSERT INTO medical_notes (title, category, content, author_id) VALUES (?, ?, ?, ?)',
                     (title, category, content, author_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Note added successfully! The new note is stored in the database.'})
    except Exception as e:
        print(f"Error adding note: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while adding the note.'}), 500
    finally:
        conn.close()

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    # Authorization check
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin privileges required to edit.'}), 403

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category = data.get('category') # Expected to be the subcategory (e.g., 'anatomy')

    conn = get_db_connection()
    try:
        # Updates are now applied to the database
        query = 'UPDATE medical_notes SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        result = conn.execute(query, (title, content, category, note_id))

        if result.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Note not found.'}), 404

        conn.commit()
        return jsonify({'success': True, 'message': 'Note updated successfully! Changes are persistent in the database.'})
    except Exception as e:
        print(f"Error updating note: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during update.'}), 500
    finally:
        conn.close()

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    # Authorization check
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin privileges required.'}), 403

    conn = get_db_connection()
    try:
        # Deletion is applied to the database
        result = conn.execute('DELETE FROM medical_notes WHERE id = ?', (note_id,))

        if result.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Note not found.'}), 404

        conn.commit()
        return jsonify({'success': True, 'message': 'Note deleted successfully from the database.'})
    except Exception as e:
        print(f"Error deleting note: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during deletion.'}), 500
    finally:
        conn.close()

# --- ADMIN DASHBOARD STATS ROUTES (Minimal Implementation) ---

@app.route('/api/admin_stats', methods=['GET'])
def admin_stats():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin privileges required.'}), 403

    conn = get_db_connection()
    
    total_notes = conn.execute("SELECT COUNT(id) FROM medical_notes").fetchone()[0]
    total_users = conn.execute("SELECT COUNT(id) FROM users").fetchone()[0]
    total_views = conn.execute("SELECT SUM(views) FROM medical_notes").fetchone()[0] or 0
    last_update = conn.execute("SELECT MAX(updated_at) FROM medical_notes").fetchone()[0]

    conn.close()
    
    stats = {
        'total_notes': total_notes,
        'total_users': total_users,
        'total_views': total_views,
        'last_update': last_update
    }

    return jsonify({'success': True, 'stats': stats})

@app.route('/api/note_views', methods=['GET'])
def get_top_notes():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin privileges required.'}), 403

    conn = get_db_connection()
    # Get top 5 most viewed notes
    top_notes = conn.execute("SELECT id, title, category, views FROM medical_notes ORDER BY views DESC LIMIT 5").fetchall()
    conn.close()
    
    return jsonify({'success': True, 'top_notes': [dict(note) for note in top_notes]})


# --- Run App ---
if __name__ == '__main__':
    # Initialize DB here for local run convenience
    init_db() 
    # Note: In production (WSGI), the @app.before_first_request hook handles initialization
    app.run(debug=True)
