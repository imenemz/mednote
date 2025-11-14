from flask import Flask, render_template, request, jsonify # Removed session, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import secrets
import time
from flask_cors import CORS # Used for front-end connectivity

# --- NEW JWT IMPORTS ---
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from datetime import timedelta
# -----------------------

# --- CRITICAL DEPLOYMENT PATH CORRECTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'clinicalroots.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# Ensure directories exist
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app = Flask(__name__,
            static_folder=os.path.join(BASE_DIR, 'frontend'),
            template_folder=os.path.join(BASE_DIR, 'frontend'))

# --- CORS and JWT Configuration ---
# CORS allows your front-end (on one port/origin) to talk to the back-end (on a different port/origin)
CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# JWT Configuration
app.config["JWT_SECRET_KEY"] = app.config['SECRET_KEY']
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24) # Tokens expire after 24 hours
jwt = JWTManager(app)


# --- Database Connection and Initialization Functions ---

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Create Users Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
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
            category TEXT NOT NULL, 
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
            ('Human Heart Structure', 'anatomy', '<h3>Overview</h3><p>The human heart is a muscular organ with four chambers.</p>', 1),
            ('Skeletal System', 'anatomy', '<h3>Overview</h3><p>The skeletal system provides structural support.</p>', 1),
            ('Nervous System Basics', 'anatomy', '<h3>Overview</h3><p>Central and peripheral nervous systems control body functions.</p>', 1),
            ('Cardiac Cycle', 'physiology', '<h3>Systole and Diastole</h3><p>Heart contraction and relaxation phases.</p>', 1),
            ('Myocardial Infarction', 'pathology', '<h3>Heart Attack</h3><p>Death of heart muscle due to blocked blood supply.</p>', 1),
            ('Acute Coronary Syndrome', 'cardiology', '<h3>Overview</h3><p>A set of conditions associated with sudden reduced blood flow to the heart.</p>', 1),
        ]

        # The loop must handle the author_id properly
        for title, category, content, author_id in sample_notes:
            c.execute('INSERT INTO medical_notes (title, category, content, author_id) VALUES (?, ?, ?, ?)', 
                      (title, category, content, author_id))
        print("Default admin user and sample data created.")

    conn.commit()
    conn.close()

@app.before_first_request
def boot():
    """Initializes the database before the first request."""
    try:
        init_db()
    except Exception as e:
        print(f"Startup database initialization error: {e}")

@app.after_request
def no_cache_for_html(resp):
    """Prevents caching of HTML files."""
    if resp.mimetype == 'text/html':
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
    return resp

@app.route('/__diag')
def __diag():
    """Returns diagnostic information."""
    idx = os.path.join(BASE_DIR, 'frontend', 'index.html')
    js  = os.path.join(BASE_DIR, 'frontend', 'app.js')

    info = {
        "py_file": __file__,
        "db_path": DB_PATH,
        "index_exists": os.path.exists(idx),
        "js_exists": os.path.exists(js),
        "jwt_secret_set": "YES" if app.config.get("JWT_SECRET_KEY") else "NO",
        "cors_enabled": "YES"
    }
    return jsonify(info)


# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main HTML file."""
    return render_template('index.html')

# ----------------------------------------------------------------------
# --- USER & JWT AUTH ROUTES (TOKEN-BASED) ---
# ----------------------------------------------------------------------

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute("SELECT id, email, password_hash, role FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        # Create JWT payload (identity)
        identity = {'id': user['id'], 'role': user['role']}
        access_token = create_access_token(identity=identity)
        
        # Return the token and user data that app.js expects
        return jsonify({
            'message': 'Login successful!',
            'token': access_token, 
            'user': {
                'id': user['id'],
                'email': user['email'],
                'role': user['role']
            }
        })

    return jsonify({'message': 'Invalid email or password'}), 401

# Logout is now stateless; the client (app.js) simply clears the token
@app.route('/api/logout', methods=['POST'])
def api_logout():
    return jsonify({'success': True, 'message': 'Logged out successfully (client token cleared)'})

@app.route('/api/change_password', methods=['POST'])
@jwt_required()
def change_password():
    current_user = get_jwt_identity()

    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT password_hash FROM users WHERE id = ?", (current_user['id'],)).fetchone()

    if not user or not check_password_hash(user['password_hash'], current_password):
        conn.close()
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

    new_password_hash = generate_password_hash(new_password)
    try:
        conn.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                     (new_password_hash, current_user['id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Password changed successfully!'})
    except Exception as e:
        print(f"Error updating password: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during password change.'}), 500
    finally:
        conn.close()


# ----------------------------------------------------------------------
# --- PUBLIC CATEGORY AND NOTE ROUTES (NO @jwt_required) ---
# ----------------------------------------------------------------------

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Retrieves all major categories and their subcategories for the main page."""
    conn = get_db_connection()
    # Get unique subcategories (which is the 'category' column) and count notes in each
    query = """
        SELECT category, COUNT(id) as note_count
        FROM medical_notes
        WHERE is_published = 1
        GROUP BY category
        ORDER BY category
    """
    categories_raw = conn.execute(query).fetchall()
    conn.close()

    def get_major_category_info(subcat_db_name):
        # Defines the top-level grouping for display
        top_level_mapping = {
            'anatomy': ('Medical', 'Structure and organization of the human body'),
            'physiology': ('Medical', 'Function of the human body systems'),
            'pathology': ('Medical', 'Study of disease'),
            'cardiology': ('Specialty', 'Heart and vascular diseases'),
            'general_surgery': ('Surgical', 'Common surgical procedures'),
        }
        
        subcat_db_name = subcat_db_name.lower()
        for prefix, info in top_level_mapping.items():
            if subcat_db_name == prefix or subcat_db_name.startswith(f"{prefix}_"):
                return info
        return ('Other', 'In-depth concepts and clinical notes.')


    # 1. Structure the data into major groups
    structured_data = {
        'Medical': [],
        'Surgical': [],
        'Specialty': [],
        'Other': [],
    }
    
    for row in categories_raw:
        subcat_db_name = row['category']
        note_count = row['note_count']
        major_cat, description = get_major_category_info(subcat_db_name)
        display_name = subcat_db_name.replace('_', ' ').title()

        if major_cat in structured_data:
            structured_data[major_cat].append({
                'name': display_name,
                'db_name': subcat_db_name,
                'notes': note_count,
                'description': description,
            })
            
    # 2. Flatten and combine the lists for the front-end (app.js expects an array of categories)
    all_categories = []
    for key in ['Medical', 'Surgical', 'Specialty', 'Other']:
        for cat in structured_data[key]:
            # Add the major group for context in the front-end (optional, but helpful)
            cat['major_group'] = key 
            all_categories.append(cat)

    return jsonify(all_categories) # Returns an array: [{name: 'Anatomy', ...}, {name: 'Cardiology', ...}]

# ----------------------------------------------------------------------
# --- PUBLIC NOTES RETRIEVAL ROUTES (Used by both user and admin) ---
# ----------------------------------------------------------------------

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Retrieves notes based on category (subcategory in this schema) or search query."""
    conn = get_db_connection()
    category = request.args.get('category')
    search_query = request.args.get('search')

    query = "SELECT id, title, category, views, updated_at FROM medical_notes WHERE is_published = 1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if search_query:
        # Simple LIKE search on title and content
        query += " AND (title LIKE ? OR content LIKE ?)"
        params.append(f'%{search_query}%')
        params.append(f'%{search_query}%')

    query += " ORDER BY updated_at DESC"

    notes = conn.execute(query, params).fetchall()
    conn.close()

    # Return as a list of dictionaries
    return jsonify([dict(note) for note in notes])

@app.route('/api/note/<int:note_id>', methods=['GET'])
def get_single_note(note_id):
    """Retrieves a single note and increments its view count."""
    conn = get_db_connection()
    
    # Select the note
    note = conn.execute("SELECT id, title, category, content, views, updated_at FROM medical_notes WHERE id = ? AND is_published = 1", (note_id,)).fetchone()

    if note is None:
        conn.close()
        return jsonify({'message': 'Note not found or not published.'}), 404

    # Increment view count
    conn.execute('UPDATE medical_notes SET views = views + 1 WHERE id = ?', (note_id,))
    conn.commit()
    
    # Re-fetch note to get updated view count (or just update the dict)
    updated_note = dict(note)
    updated_note['views'] += 1 # Update locally before returning
    
    conn.close()

    # NOTE: app.js expects the note object directly, not wrapped in {'note': ...}
    return jsonify(updated_note) 


# ----------------------------------------------------------------------
# --- ADMIN ONLY ROUTES (PROTECTED BY @jwt_required) ---
# ----------------------------------------------------------------------

@app.route('/api/categories/all', methods=['GET'])
@jwt_required()
def get_all_categories_admin():
    """Retrieves a list of all unique category names for admin selection."""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin privileges required.'}), 403
        
    conn = get_db_connection()
    
    # Get all unique categories currently in the notes table
    categories = conn.execute("SELECT DISTINCT category FROM medical_notes ORDER BY category").fetchall()
    conn.close()
    
    category_list = [c['category'] for c in categories]
    major_categories = ['anatomy', 'physiology', 'pathology', 'pharmacology', 
                        'general_surgery', 'orthopedics', 'neurosurgery', 
                        'cardiology', 'neurology', 'endocrinology']
    
    all_parent_categories = sorted(list(set(category_list + major_categories)))
    
    return jsonify(all_parent_categories) # Returns a flat array of strings

@app.route('/api/note', methods=['POST'])
@jwt_required()
def add_note():
    """Adds a new note (Admin only)."""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin privileges required to add notes.'}), 403

    data = request.get_json()
    title = data.get('title')
    category = data.get('category')
    content = data.get('content')
    author_id = current_user['id'] # Get author ID from the JWT token

    if not title or not category or not content:
        return jsonify({'message': 'Title, category, and content are required.'}), 400

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO medical_notes (title, category, content, author_id) VALUES (?, ?, ?, ?)',
                     (title, category, content, author_id))
        conn.commit()
        return jsonify({'message': 'Note added successfully!'})
    except Exception as e:
        print(f"Error adding note: {e}")
        return jsonify({'message': 'An error occurred while adding the note.'}), 500
    finally:
        conn.close()

@app.route('/api/note/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(note_id):
    """Updates an existing note (Admin only)."""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin privileges required to edit.'}), 403

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category = data.get('category')

    conn = get_db_connection()
    try:
        # Note: We include category update here, as the front-end form may not update it
        query = 'UPDATE medical_notes SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        result = conn.execute(query, (title, content, category, note_id))

        if result.rowcount == 0:
            conn.close()
            return jsonify({'message': 'Note not found.'}), 404

        conn.commit()
        return jsonify({'message': 'Note updated successfully!'})
    except Exception as e:
        print(f"Error updating note: {e}")
        return jsonify({'message': 'An error occurred during update.'}), 500
    finally:
        conn.close()

@app.route('/api/note/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    """Deletes a note (Admin only)."""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin privileges required.'}), 403

    conn = get_db_connection()
    try:
        result = conn.execute('DELETE FROM medical_notes WHERE id = ?', (note_id,))

        if result.rowcount == 0:
            conn.close()
            return jsonify({'message': 'Note not found.'}), 404

        conn.commit()
        return jsonify({'message': 'Note deleted successfully.'})
    except Exception as e:
        print(f"Error deleting note: {e}")
        return jsonify({'message': 'An error occurred during deletion.'}), 500
    finally:
        conn.close()

# ----------------------------------------------------------------------
# --- ADMIN DASHBOARD STATS ROUTES (PROTECTED) ---
# ----------------------------------------------------------------------

@app.route('/api/admin_stats', methods=['GET'])
@jwt_required()
def admin_stats():
    """Retrieves basic stats for the dashboard (Admin only)."""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin privileges required.'}), 403

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

    return jsonify(stats)

@app.route('/api/note_views', methods=['GET'])
@jwt_required()
def get_top_notes():
    """Retrieves the top viewed notes (Admin only)."""
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin privileges required.'}), 403

    conn = get_db_connection()
    # Get top 5 most viewed notes
    top_notes = conn.execute("SELECT id, title, category, views FROM medical_notes ORDER BY views DESC LIMIT 5").fetchall()
    conn.close()

    return jsonify([dict(note) for note in top_notes])


# --- Run App ---
if __name__ == '__main__':
    init_db()
    # Run the app
    app.run(debug=True)