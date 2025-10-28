from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import secrets

# --- CRITICAL DEPLOYMENT PATH CORRECTION ---
# Define the base directory of the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'medmaster.db')
# ----------------------------------------

# Ensure the database directory exists
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)


app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER,
            views INTEGER DEFAULT 0,
            is_published BOOLEAN DEFAULT 1, -- Default to published
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    """)

    # 3. Check for and Create Default Admin User
    c.execute("SELECT * FROM users WHERE email = 'imenemazouz05@gmail.com'")
    if c.fetchone() is None:
        admin_password_hash = generate_password_hash('zainhanouni2005')
        c.execute("INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                  ('admin_user', 'imenemazouz05@gmail.com', admin_password_hash, 'admin'))

        # Insert sample data (Admin ID is 1 if it's the first user)
        sample_notes = [
            ('Human Heart Structure', 'anatomy', '<h3>Overview</h3><p>The human heart is a muscular organ with four chambers.</p>'),
            ('Skeletal System', 'anatomy', '<h3>Overview</h3><p>The skeletal system provides structural support.</p>'),
            ('Nervous System Basics', 'anatomy', '<h3>Overview</h3><p>Central and peripheral nervous systems control body functions.</p>'),
            ('Cardiac Cycle', 'physiology', '<h3>Systole and Diastole</h3><p>Heart contraction and relaxation phases.</p>'),
            ('Respiratory Function', 'physiology', '<h3>Gas Exchange</h3><p>Oxygen and carbon dioxide exchange in lungs.</p>'),
            ('Myocardial Infarction', 'pathology', '<h3>Heart Attack</h3><p>Death of heart muscle due to blocked blood supply.</p>'),
            ('Pneumonia', 'pathology', '<h3>Lung Infection</h3><p>Bacterial or viral infection of lung tissue.</p>')
        ]

        # Note: We assume the admin_user is id=1, which is safe on first run
        for note in sample_notes:
            c.execute('INSERT INTO medical_notes (title, category, content, author_id) VALUES (?, ?, ?, 1)', note)

        print("Default admin user and sample data created.")

    conn.commit()
    conn.close()

# --- Flask Routes ---

@app.route('/')
def index():
    # Renders the main frontend page
    return render_template('index.html')


# --- CRITICAL: JSON API Login Endpoint (for app.js) ---
@app.route('/api/login', methods=['POST'])
def api_login():
    # Expects JSON data from the frontend
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['logged_in'] = True
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['email'] = user['email']

        # Return necessary user info to the frontend for sessionStorage
        return jsonify({'success': True, 'role': user['role'], 'email': user['email']})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})


@app.route('/admin')
def admin_dashboard():
    # Simple check for admin role
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        # Use redirect to the index which will handle the login view
        return redirect(url_for('index'))

    conn = get_db_connection()

    total_notes = conn.execute("SELECT COUNT(*) FROM medical_notes").fetchone()['COUNT(*)']
    total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'user'").fetchone()['COUNT(*)']
    total_views = conn.execute("SELECT SUM(views) FROM medical_notes").fetchone()[0] or 0
    recent_notes = conn.execute("SELECT * FROM medical_notes ORDER BY created_at DESC LIMIT 10").fetchall()

    conn.close()

    # Pass the variables to the template (admin_dashboard.html)
    return render_template('admin_dashboard.html',
                         total_notes=total_notes,
                         total_students=total_students,
                         total_views=total_views,
                         recent_notes=recent_notes)


@app.route('/api/notes/<category>')
def get_notes_by_category(category):
    conn = get_db_connection()

    # Check if admin is logged in. Admins can see unpublished notes.
    is_admin = session.get('role') == 'admin'

    query = 'SELECT id, title, content, views, created_at FROM medical_notes WHERE category = ?'
    params = [category]

    if not is_admin:
        query += ' AND is_published = 1' # Only published notes for public/user

    query += ' ORDER BY created_at DESC'

    notes = []
    # Execute with correct parameter binding
    for row in conn.execute(query, params).fetchall():
        notes.append({
            # Access columns by name thanks to conn.row_factory = sqlite3.Row
            'id': row['id'],
            'title': row['title'],
            'content': row['content'],
            'views': row['views'],
            'created_at': row['created_at']
        })

    conn.close()
    return jsonify(notes)


# --- NEW ROUTE: Admin In-Place Content Editor Save (PUT) ---
@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    # Authorization: Only Admin can edit
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin privileges required to edit.'}), 403

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    conn = get_db_connection()
    existing_note = conn.execute('SELECT * FROM medical_notes WHERE id = ?', (note_id,)).fetchone()

    if not existing_note:
        conn.close()
        return jsonify({'success': False, 'message': 'Note not found.'}), 404

    # Use existing category and publication status, unless explicitly provided
    category = data.get('category', existing_note['category'])
    is_published = data.get('is_published', existing_note['is_published'])

    try:
        conn.execute("""
            UPDATE medical_notes
            SET title = ?, content = ?, category = ?, is_published = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, content, category, is_published, note_id))
        conn.commit()
        return jsonify({'success': True, 'message': f'Note ID {note_id} updated successfully.'})
    except Exception as e:
        print(f"Error updating note: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during update.'}), 500
    finally:
        conn.close()


# --- Admin Add New Note (POST) ---
@app.route('/api/notes', methods=['POST'])
def add_new_note():
    # Authorization: Only Admin can add notes
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin privileges required.'}), 403

    data = request.get_json()
    title = data.get('title')
    category = data.get('category')
    content = data.get('content')
    is_published = data.get('is_published', 0) # Default to unpublished

    if not all([title, category, content]):
        return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO medical_notes (title, category, content, author_id, is_published)
            VALUES (?, ?, ?, ?, ?)
        """, (title, category, content, session['user_id'], is_published))
        conn.commit()
        return jsonify({'success': True, 'message': 'Note added successfully!'})
    except Exception as e:
        print(f"Error adding new note: {e}")
        return jsonify({'success': False, 'message': 'An error occurred.'}), 500
    finally:
        conn.close()


# --- Password Change Endpoint (API, better for frontend) ---
@app.route('/api/change-password', methods=['POST'])
def api_change_password():
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

# --- Run App ---
if __name__ == '__main__':
    # The database has already been initialized on the server via a manual python run.
    # We leave this line only to allow local testing if needed, but the line below MUST be commented out for deployment.
    # init_db()

    # ------------------------------------------------------------------------------------------------
    # CRITICAL: Comment out or remove the app.run() line for production deployment with Gunicorn/WSGI
    # app.run(debug=True, host='0.0.0.0', port=5000)
    # ------------------------------------------------------------------------------------------------

    pass # Ensures the file ends cleanly
