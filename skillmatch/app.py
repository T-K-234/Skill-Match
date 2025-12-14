from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Create users table if it doesn't exist
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Users table already exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('student', 'employee')) NOT NULL
        )
    ''')


    c.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skill TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # New: certificates table
    c.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            certificate TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # New: jobs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employer_id INTEGER,
            job_title TEXT,
            required_skills TEXT,
            FOREIGN KEY(employer_id) REFERENCES users(id)
        )
    ''')

        # Applications table
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            job_id INTEGER,
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(job_id) REFERENCES jobs(id),
            UNIQUE(student_id, job_id)  -- prevent duplicate applications
        )
    ''')


    conn.commit()
    conn.close()


init_db()

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            conn.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]

            flash(f"Welcome, {user[1]}!", 'success')

            # Redirect based on role
            if user[3] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user[3] == 'employee':
                return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')



from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def compute_skill_match(student_skills, job_skills):
    # Convert both lists into a single string (comma-separated)
    student_text = ', '.join([s.strip().lower() for s in student_skills])
    job_text = ', '.join([s.strip().lower() for s in job_skills])
    
    # Encode the texts using BERT embeddings
    student_embedding = model.encode(student_text, convert_to_tensor=True)
    job_embedding = model.encode(job_text, convert_to_tensor=True)
    
    # Compute cosine similarity using semantic embeddings
    similarity_score = util.pytorch_cos_sim(student_embedding, job_embedding).item()
    match_score = round(similarity_score * 100, 2)
    
    # Find missing or weakly matching skills semantically
    missing_skills = []
    for js in job_skills:
        js_embed = model.encode(js.lower(), convert_to_tensor=True)
        max_sim = max([util.pytorch_cos_sim(js_embed, model.encode(ss.lower(), convert_to_tensor=True)).item() for ss in student_skills])
        if max_sim < 0.6:  # threshold to mark as missing
            missing_skills.append(js)

    return match_score, missing_skills



@app.route('/student/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Handle skill/cert/job application form submissions
    if request.method == 'POST':
        if 'skill' in request.form:
            skill = request.form['skill']
            c.execute("INSERT INTO skills (user_id, skill) VALUES (?, ?)", (user_id, skill))
        elif 'certification' in request.form:
            cert = request.form['certification']
            c.execute("INSERT INTO certificates (user_id, certificate) VALUES (?, ?)", (user_id, cert))
        elif 'apply_job_id' in request.form:
            job_id = int(request.form['apply_job_id'])
            try:
                c.execute("INSERT INTO applications (student_id, job_id) VALUES (?, ?)", (user_id, job_id))
                flash("Applied successfully!", "success")
            except sqlite3.IntegrityError:
                flash("You have already applied for this job.", "warning")
        conn.commit()

    # Fetch student data
    c.execute("SELECT skill FROM skills WHERE user_id = ?", (user_id,))
    skills = [row[0] for row in c.fetchall()]

    c.execute("SELECT certificate FROM certificates WHERE user_id = ?", (user_id,))
    certs = [row[0] for row in c.fetchall()]

    # Fetch jobs
    c.execute("SELECT id, job_title, required_skills FROM jobs")
    jobs = c.fetchall()

    # Fetch applied job IDs
    c.execute("SELECT job_id FROM applications WHERE student_id = ?", (user_id,))
    applied_job_ids = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template(
        'student_dashboard.html',
        username=session['username'],
        skills=skills,
        certs=certs,
        jobs=jobs,
        applied_job_ids=applied_job_ids
    )


@app.route('/employee/dashboard', methods=['GET', 'POST'])
def employee_dashboard():
    if session.get('role') != 'employee':
        return redirect(url_for('login'))

    employer_id = session['user_id']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Handle job posting form
    if request.method == 'POST':
        job_title = request.form['job_title']
        required_skills = request.form['required_skills']
        c.execute("INSERT INTO jobs (employer_id, job_title, required_skills) VALUES (?, ?, ?)",
                  (employer_id, job_title, required_skills))
        conn.commit()

    # Get all jobs posted by the employer
    c.execute("SELECT id, job_title, required_skills FROM jobs WHERE employer_id = ?", (employer_id,))
    jobs = c.fetchall()

    # For each job, get applicants (with their skills)
    job_applicants = {}
    for job in jobs:
        job_id = job[0]
        c.execute('''
            SELECT users.username, GROUP_CONCAT(skills.skill)
            FROM applications
            JOIN users ON users.id = applications.student_id
            LEFT JOIN skills ON users.id = skills.user_id
            WHERE applications.job_id = ?
            GROUP BY users.id
        ''', (job_id,))
        applicants = c.fetchall()
        job_applicants[job_id] = applicants

    conn.close()

    return render_template('employee_dashboard.html', username=session['username'], jobs=jobs, job_applicants=job_applicants)

@app.route('/match/<int:job_id>')
def match_skills(job_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Get student's skills
    c.execute("SELECT skill FROM skills WHERE user_id = ?", (user_id,))
    student_skills = [row[0] for row in c.fetchall()]

    # Get job's required skills
    c.execute("SELECT job_title, required_skills FROM jobs WHERE id = ?", (job_id,))
    job = c.fetchone()
    job_title = job[0]
    job_skills = [s.strip() for s in job[1].split(',')]

    conn.close()

    match_score, missing_skills = compute_skill_match(student_skills, job_skills)

    return render_template(
        'match_result.html',
        job_title=job_title,
        match_score=match_score,
        missing_skills=missing_skills,
        student_skills=student_skills,
        job_skills=job_skills
    )


if __name__ == '__main__':
    app.run(debug=True)
