from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import secrets

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect('database/medmaster.db')
    c = conn.cursor()

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

    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER,
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_published BOOLEAN DEFAULT 1,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    """)

    # Check if admin exists, if not create with new credentials
    c.execute("SELECT * FROM users WHERE role = 'admin'")
    admin_exists = c.fetchone()

    if not admin_exists:
        # NEW ADMIN CREDENTIALS AS REQUESTED
        admin_hash = generate_password_hash('Zain%2005')
        c.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                 ('Admin', 'imenemazouz05@gmail.com', admin_hash, 'admin'))

        sample_notes = [
            ('Human Heart Structure', 'anatomy', '<h3>Overview</h3><p>The human heart is a muscular organ with four chambers.</p>'),
            ('Skeletal System', 'anatomy', '<h3>Overview</h3><p>The skeletal system provides structural support.</p>'),
            ('Nervous System Basics', 'anatomy', '<h3>Overview</h3><p>Central and peripheral nervous systems control body functions.</p>'),
            ('Cardiac Cycle', 'physiology', '<h3>Systole and Diastole</h3><p>Heart contraction and relaxation phases.</p>'),
            ('Respiratory Function', 'physiology', '<h3>Gas Exchange</h3><p>Oxygen and carbon dioxide exchange in lungs.</p>'),
            ('Myocardial Infarction', 'pathology', '<h3>Heart Attack</h3><p>Death of heart muscle due to blocked blood supply.</p>'),
            ('Pneumonia', 'pathology', '<h3>Lung Infection</h3><p>Bacterial or viral infection of lung tissue.</p>')
        ]

        for note in sample_notes:
            c.execute('INSERT INTO medical_notes (title, category, content, author_id) VALUES (?, ?, ?, 1)', note)

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database/medmaster.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard' if user[4] == 'admin' else 'index'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database/medmaster.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email = ? OR username = ?", (email, username))
        existing_user = c.fetchone()

        if existing_user:
            flash('User with this email or username already exists', 'error')
        else:
            password_hash = generate_password_hash(password)
            c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                     (username, email, password_hash))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            conn.close()
            return redirect(url_for('login'))

        conn.close()

    return render_template('register.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Password change functionality for all users"""
    if 'user_id' not in session:
        flash('Please login to change your password', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Validate new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('change_password.html')

        # Validate password strength
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('change_password.html')

        conn = sqlite3.connect('database/medmaster.db')
        c = conn.cursor()

        # Get current user
        c.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()

        if not user or not check_password_hash(user[3], current_password):
            flash('Current password is incorrect', 'error')
            conn.close()
            return render_template('change_password.html')

        # Update password
        new_password_hash = generate_password_hash(new_password)
        c.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                 (new_password_hash, session['user_id']))
        conn.commit()
        conn.close()

        flash('Password changed successfully!', 'success')
        return redirect(url_for('admin_dashboard' if session.get('role') == 'admin' else 'index'))

    return render_template('change_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database/medmaster.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM medical_notes")
    total_notes = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
    total_students = c.fetchone()[0]

    c.execute("SELECT SUM(views) FROM medical_notes")
    total_views = c.fetchone()[0] or 0

    c.execute("SELECT * FROM medical_notes ORDER BY created_at DESC LIMIT 10")
    recent_notes = c.fetchall()

    conn.close()

    return render_template('admin_dashboard.html', 
                         total_notes=total_notes, 
                         total_students=total_students,
                         total_views=total_views,
                         recent_notes=recent_notes)

@app.route('/api/notes/<category>')
def get_notes_by_category(category):
    conn = sqlite3.connect('database/medmaster.db')
    c = conn.cursor()

    c.execute('SELECT id, title, content, views, created_at FROM medical_notes WHERE category = ? AND is_published = 1 ORDER BY created_at DESC', (category,))

    notes = []
    for row in c.fetchall():
        notes.append({
            'id': row[0],
            'title': row[1], 
            'content': row[2],
            'views': row[3],
            'created_at': row[4]
        })

    conn.close()
    return jsonify(notes)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
