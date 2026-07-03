from flask import Flask, render_template, request, redirect, session, url_for,flash
import sqlite3
from werkzeug.utils import secure_filename
import os
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = "secret"  # needed for flash messages

DB = "complaints.db"

def get_db_connection():
    conn = sqlite3.connect(
        "complaints.db",
        timeout=10,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn

# Home Page → Complaint Form
@app.route('/')
def index():
    return render_template('index.html')

# Admin Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        user=conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('index'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('username') 
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("Email already registered!", "error")
                return redirect(url_for('register'))

            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
            flash("Registered successfully! Please login.", "success")
            return redirect(url_for('login'))

        except sqlite3.Error as e:
            conn.rollback()
            flash("Database error. Please try again.", "error")
            return redirect(url_for('register'))

        finally:
            conn.close()

    return render_template('register.html')


# Forgot Password Page
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        conn = get_db_connection()
        user=conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user:
            flash("Password reset instructions sent to your email.", "success")
        else:
            flash("Email not found.", "error")
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

# Thank You Page after complaint submission
@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

# Admin Dashboard (just static for now)
@app.route('/admin')
def admin():

    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    if search:
        complaints = conn.execute("""
                                  SELECT * FROM complaints
                                  WHERE name LIKE ?
                                  OR email LIKE ?
                                  OR category LIKE ?
                                  ORDER BY id DESC
                                  """, (
                                      f'%{search}%',
                                      f'%{search}%',
                                      f'%{search}%'
                                      )).fetchall()
    elif status_filter:
        complaints = conn.execute("""
                                  SELECT * FROM complaints
                                  WHERE status = ?
                                  ORDER BY id DESC
                                  """, (status_filter,)).fetchall()
    else:
        complaints = conn.execute(
            "SELECT * FROM complaints ORDER BY id DESC"
            ).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status='Pending'"
    ).fetchone()[0]

    progress = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status='In Progress'"
    ).fetchone()[0]

    resolved = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status='Resolved'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        'admin.html',
        complaints=complaints,
        total=total,
        pending=pending,
        progress=progress,
        resolved=resolved
    )
# Optional: handle 404 errors nicely
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>Page Not Found</h1><p>Check your URL or go back to <a href='/'>Home</a>.</p>", 404

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    name = request.form.get('name')
    email = request.form.get('email')
    category = request.form.get('category')
    description = request.form.get('description')
    location = request.form.get('location')
    image = request.files['image']
    filename = secure_filename(image.filename)
    upload_folder = 'uploads'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    image_path = os.path.join(upload_folder, filename)
    image.save(image_path)
    print(name, email, category, description, location)
    print("Database location:", os.path.abspath("complaints.db"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO complaints (name, email, category, description, location,file_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, category, description, location,filename))

    conn.commit()
    all_rows = conn.execute("SELECT * FROM complaints").fetchall()
    print("All complaints:", all_rows)
    conn.close()

    return redirect(url_for('thankyou'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):

    status = request.form.get('status')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE complaints SET status = ? WHERE id = ?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('admin'))

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))

@app.route('/track', methods=['GET', 'POST'])
def track():

    complaints = None

    if request.method == 'POST':

        email = request.form.get('email')

        conn = get_db_connection()

        complaints = conn.execute("""
            SELECT * FROM complaints
            WHERE email = ?
            ORDER BY id DESC
        """, (email,)).fetchall()

        conn.close()

    return render_template(
        'track.html',
        complaints=complaints
    )

@app.route('/delete/<int:id>')
def delete_complaint(id):

    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM complaints WHERE id = ?",
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect(url_for('admin'))

if __name__ == "__main__":
    app.run(debug=False)
