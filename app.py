from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from datetime import date

app = Flask(__name__)

DB_NAME = "placement.db"


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    # Applications table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT DEFAULT '',
            application_date TEXT DEFAULT '',
            status TEXT DEFAULT 'Applied',
            interview_date TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
    """)

    # Preparation tasks
    conn.execute("""
        CREATE TABLE IF NOT EXISTS preparation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            category TEXT DEFAULT '',
            completed INTEGER DEFAULT 0
        )
    """)

    # Company notes
    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            topic TEXT NOT NULL,
            notes TEXT DEFAULT ''
        )
    """)

    conn.commit()

    # -----------------------------------------------------
    # FIX OLD DATABASES
    # -----------------------------------------------------
    # If your old database does not have these columns,
    # add them automatically.
    
    columns = conn.execute(
        "PRAGMA table_info(applications)"
    ).fetchall()

    existing_columns = [column["name"] for column in columns]

    if "location" not in existing_columns:
        conn.execute(
            "ALTER TABLE applications ADD COLUMN location TEXT DEFAULT ''"
        )

    if "application_date" not in existing_columns:
        conn.execute(
            "ALTER TABLE applications ADD COLUMN application_date TEXT DEFAULT ''"
        )

    if "status" not in existing_columns:
        conn.execute(
            "ALTER TABLE applications ADD COLUMN status TEXT DEFAULT 'Applied'"
        )

    if "interview_date" not in existing_columns:
        conn.execute(
            "ALTER TABLE applications ADD COLUMN interview_date TEXT DEFAULT ''"
        )

    if "notes" not in existing_columns:
        conn.execute(
            "ALTER TABLE applications ADD COLUMN notes TEXT DEFAULT ''"
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# COMMON HTML
# ---------------------------------------------------------

STYLE = """
<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: #f4f7fb;
    color: #1f2937;
}

.navbar {
    background: #111827;
    color: white;
    padding: 18px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.navbar h1 {
    margin: 0;
    font-size: 22px;
}

.navbar a {
    color: white;
    text-decoration: none;
    margin-left: 22px;
    font-size: 14px;
}

.container {
    width: 92%;
    max-width: 1200px;
    margin: 30px auto;
}

h2 {
    margin-bottom: 5px;
}

.subtitle {
    color: #6b7280;
    margin-bottom: 25px;
}

.cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin-bottom: 30px;
}

.card {
    background: white;
    border-radius: 12px;
    padding: 22px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.06);
}

.card h3 {
    margin: 0;
    color: #6b7280;
    font-size: 14px;
}

.number {
    font-size: 30px;
    font-weight: bold;
    margin-top: 10px;
}

.section {
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 25px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.06);
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}

.btn {
    display: inline-block;
    padding: 10px 16px;
    background: #2563eb;
    color: white;
    text-decoration: none;
    border: none;
    border-radius: 7px;
    cursor: pointer;
}

.btn:hover {
    background: #1d4ed8;
}

.btn-danger {
    background: #dc2626;
}

.btn-danger:hover {
    background: #b91c1c;
}

.btn-green {
    background: #16a34a;
}

.btn-small {
    padding: 7px 10px;
    font-size: 12px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    text-align: left;
    padding: 13px 10px;
    border-bottom: 1px solid #e5e7eb;
}

th {
    background: #f9fafb;
    font-size: 13px;
}

.status {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}

.Applied {
    background: #dbeafe;
    color: #1d4ed8;
}

.Shortlisted {
    background: #fef3c7;
    color: #92400e;
}

.Interview {
    background: #ede9fe;
    color: #6d28d9;
}

.Selected {
    background: #dcfce7;
    color: #166534;
}

.Rejected {
    background: #fee2e2;
    color: #991b1b;
}

form {
    max-width: 800px;
}

label {
    display: block;
    margin-top: 15px;
    margin-bottom: 6px;
    font-weight: bold;
}

input, select, textarea {
    width: 100%;
    padding: 11px;
    border: 1px solid #d1d5db;
    border-radius: 7px;
    font-size: 14px;
}

textarea {
    min-height: 100px;
    resize: vertical;
}

.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}

.task {
    display: flex;
    align-items: center;
    padding: 13px;
    border-bottom: 1px solid #eee;
}

.task input {
    width: auto;
    margin-right: 10px;
}

.completed {
    text-decoration: line-through;
    color: #9ca3af;
}

.progress {
    width: 100%;
    height: 18px;
    background: #e5e7eb;
    border-radius: 20px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: #2563eb;
    text-align: center;
    color: white;
    font-size: 11px;
    line-height: 18px;
}

.note-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 12px;
}

.note-card h4 {
    margin-top: 0;
}

.empty {
    text-align: center;
    color: #9ca3af;
    padding: 25px;
}

@media(max-width: 800px) {
    .cards {
        grid-template-columns: 1fr 1fr;
    }

    .form-grid {
        grid-template-columns: 1fr;
    }

    table {
        font-size: 12px;
    }
}
</style>
"""


NAVBAR = """
<div class="navbar">
    <h1>🎓 Placement Tracker</h1>
    <div>
        <a href="/">Dashboard</a>
        <a href="/applications">Applications</a>
        <a href="/preparation">Preparation</a>
        <a href="/company-notes">Company Notes</a>
    </div>
</div>
"""


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route("/")
def dashboard():

    conn = get_db()

    applications = conn.execute("""
        SELECT * FROM applications
        ORDER BY id DESC
    """).fetchall()

    tasks = conn.execute("""
        SELECT * FROM preparation
    """).fetchall()

    total = len(applications)

    interviews = sum(
        1 for a in applications
        if a["status"] == "Interview"
    )

    selected = sum(
        1 for a in applications
        if a["status"] == "Selected"
    )

    completed = sum(
        1 for t in tasks
        if t["completed"] == 1
    )

    preparation_progress = (
        int((completed / len(tasks)) * 100)
        if tasks else 0
    )

    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Placement Dashboard</title>
        {{ style|safe }}
    </head>

    <body>

    {{ navbar|safe }}

    <div class="container">

        <h2>Student Placement Dashboard</h2>

        <p class="subtitle">
            Track your placement applications and preparation progress.
        </p>

        <div class="cards">

            <div class="card">
                <h3>Total Applications</h3>
                <div class="number">{{ total }}</div>
            </div>

            <div class="card">
                <h3>Interviews</h3>
                <div class="number">{{ interviews }}</div>
            </div>

            <div class="card">
                <h3>Selected</h3>
                <div class="number">{{ selected }}</div>
            </div>

            <div class="card">
                <h3>Preparation</h3>
                <div class="number">{{ preparation_progress }}%</div>
            </div>

        </div>


        <div class="section">

            <div class="section-header">

                <h3>Preparation Progress</h3>

                <a class="btn"
                   href="/preparation">
                    Manage Preparation
                </a>

            </div>

            <div class="progress">

                <div class="progress-bar"
                     style="width: {{ preparation_progress }}%;">
                    {{ preparation_progress }}%
                </div>

            </div>

        </div>


        <div class="section">

            <div class="section-header">

                <h3>Recent Applications</h3>

                <a class="btn"
                   href="/add-application">
                    + Add Application
                </a>

            </div>

            {% if applications %}

            <table>

                <tr>
                    <th>Company</th>
                    <th>Role</th>
                    <th>Location</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>

                {% for application in applications[:10] %}

                <tr>

                    <td>
                        <strong>
                            {{ application["company"] }}
                        </strong>
                    </td>

                    <td>
                        {{ application["role"] }}
                    </td>

                    <td>
                        {{ application["location"] or "-" }}
                    </td>

                    <td>
                        {{ application["application_date"] or "-" }}
                    </td>

                    <td>

                        <span class="status {{ application['status'] }}">
                            {{ application["status"] }}
                        </span>

                    </td>

                    <td>

                        <a class="btn btn-small"
                           href="/edit-application/{{ application['id'] }}">
                           Edit
                        </a>

                        <a class="btn btn-danger btn-small"
                           href="/delete-application/{{ application['id'] }}"
                           onclick="return confirm('Delete this application?')">
                           Delete
                        </a>

                    </td>

                </tr>

                {% endfor %}

            </table>

            {% else %}

            <div class="empty">
                No applications added yet.
            </div>

            {% endif %}

        </div>

    </div>

    </body>
    </html>
    """, style=STYLE, navbar=NAVBAR,
       applications=applications,
       total=total,
       interviews=interviews,
       selected=selected,
       preparation_progress=preparation_progress)


# ---------------------------------------------------------
# ALL APPLICATIONS
# ---------------------------------------------------------

@app.route("/applications")
def applications():

    conn = get_db()

    data = conn.execute("""
        SELECT * FROM applications
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Applications</title>
        {{ style|safe }}
    </head>

    <body>

    {{ navbar|safe }}

    <div class="container">

        <div class="section-header">
            <div>
                <h2>Placement Applications</h2>
                <p class="subtitle">
                    Keep track of every company you apply to.
                </p>
            </div>

            <a class="btn" href="/add-application">
                + Add Application
            </a>
        </div>

        <div class="section">

        {% if applications %}

        <table>

            <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Location</th>
                <th>Applied</th>
                <th>Interview</th>
                <th>Status</th>
                <th>Notes</th>
                <th>Actions</th>
            </tr>

            {% for application in applications %}

            <tr>

                <td>
                    <strong>{{ application["company"] }}</strong>
                </td>

                <td>{{ application["role"] }}</td>

                <td>
                    {{ application["location"] or "-" }}
                </td>

                <td>
                    {{ application["application_date"] or "-" }}
                </td>

                <td>
                    {{ application["interview_date"] or "-" }}
                </td>

                <td>
                    <span class="status {{ application['status'] }}">
                        {{ application["status"] }}
                    </span>
                </td>

                <td>
                    {{ application["notes"] or "-" }}
                </td>

                <td>

                    <a class="btn btn-small"
                       href="/edit-application/{{ application['id'] }}">
                       Edit
                    </a>

                    <a class="btn btn-danger btn-small"
                       href="/delete-application/{{ application['id'] }}"
                       onclick="return confirm('Delete application?')">
                       Delete
                    </a>

                </td>

            </tr>

            {% endfor %}

        </table>

        {% else %}

        <div class="empty">
            No applications available.
        </div>

        {% endif %}

        </div>

    </div>

    </body>
    </html>
    """, style=STYLE, navbar=NAVBAR,
       applications=data)


# ---------------------------------------------------------
# ADD APPLICATION
# ---------------------------------------------------------

@app.route("/add-application", methods=["GET", "POST"])
def add_application():

    if request.method == "POST":

        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()
        location = request.form.get("location", "").strip()
        application_date = request.form.get("application_date", "")
        status = request.form.get("status", "Applied")
        interview_date = request.form.get("interview_date", "")
        notes = request.form.get("notes", "").strip()

        if company and role:

            conn = get_db()

            conn.execute("""
                INSERT INTO applications
                (company, role, location, application_date,
                 status, interview_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                company,
                role,
                location,
                application_date,
                status,
                interview_date,
                notes
            ))

            conn.commit()
            conn.close()

            return redirect(url_for("applications"))

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Application</title>
        {{ style|safe }}
    </head>

    <body>

    {{ navbar|safe }}

    <div class="container">

        <div class="section">

            <h2>Add Placement Application</h2>

            <p class="subtitle">
                Add a company that you have applied to.
            </p>

            <form method="POST">

                <div class="form-grid">

                    <div>
                        <label>Company Name</label>

                        <input type="text"
                               name="company"
                               placeholder="Example: Amazon"
                               required>
                    </div>

                    <div>
                        <label>Job Role</label>

                        <input type="text"
                               name="role"
                               placeholder="Example: Software Developer"
                               required>
                    </div>

                    <div>
                        <label>Location</label>

                        <input type="text"
                               name="location"
                               placeholder="Example: Hyderabad">
                    </div>

                    <div>
                        <label>Application Date</label>

                        <input type="date"
                               name="application_date"
                               value="{{ today }}">
                    </div>

                    <div>
                        <label>Status</label>

                        <select name="status">

                            <option>Applied</option>
                            <option>Shortlisted</option>
                            <option>Interview</option>
                            <option>Selected</option>
                            <option>Rejected</option>

                        </select>

                    </div>

                    <div>
                        <label>Interview Date</label>

                        <input type="date"
                               name="interview_date">

                    </div>

                </div>

                <label>Notes</label>

                <textarea
                    name="notes"
                    placeholder="Example: Prepare Python, SQL and HR questions..."></textarea>

                <br><br>

                <button class="btn" type="submit">
                    Save Application
                </button>

                <a class="btn"
                   href="/applications">
                    Cancel
                </a>

            </form>

        </div>

    </div>

    </body>
    </html>
    """, style=STYLE, navbar=NAVBAR,
       today=date.today().isoformat())


# ---------------------------------------------------------
# EDIT APPLICATION
# ---------------------------------------------------------

@app.route("/edit-application/<int:application_id>", methods=["GET", "POST"])
def edit_application(application_id):

    conn = get_db()

    application = conn.execute("""
        SELECT * FROM applications
        WHERE id = ?
    """, (application_id,)).fetchone()

    if not application:
        conn.close()
        return "Application not found", 404

    if request.method == "POST":

        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()
        location = request.form.get("location", "").strip()
        application_date = request.form.get("application_date", "")
        status = request.form.get("status", "Applied")
        interview_date = request.form.get("interview_date", "")
        notes = request.form.get("notes", "").strip()

        conn.execute("""
            UPDATE applications

            SET company = ?,
                role = ?,
                location = ?,
                application_date = ?,
                status = ?,
                interview_date = ?,
                notes = ?

            WHERE id = ?

        """, (
            company,
            role,
            location,
            application_date,
            status,
            interview_date,
            notes,
            application_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("applications"))

    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Application</title>
        {{ style|safe }}
    </head>

    <body>

    {{ navbar|safe }}

    <div class="container">

        <div class="section">

            <h2>Edit Application</h2>

            <form method="POST">

                <div class="form-grid">

                    <div>

                        <label>Company</label>

                        <input type="text"
                               name="company"
                               value="{{ application['company'] }}"
                               required>

                    </div>

                    <div>

                        <label>Role</label>

                        <input type="text"
                               name="role"
                               value="{{ application['role'] }}"
                               required>

                    </div>

                    <div>

                        <label>Location</label>

                        <input type="text"
                               name="location"
                               value="{{ application['location'] or '' }}">

                    </div>

                    <div>

                        <label>Application Date</label>

                        <input type="date"
                               name="application_date"
                               value="{{ application['application_date'] or '' }}">

                    </div>

                    <div>

                        <label>Status</label>

                        <select name="status">

                            {% for s in ['Applied','Shortlisted','Interview','Selected','Rejected'] %}

                            <option value="{{ s }}"
                                {% if application['status'] == s %}
                                selected
                                {% endif %}>

                                {{ s }}

                            </option>

                            {% endfor %}

                        </select>

                    </div>

                    <div>

                        <label>Interview Date</label>

                        <input type="date"
                               name="interview_date"
                               value="{{ application['interview_date'] or '' }}">

                    </div>

                </div>

                <label>Notes</label>

                <textarea name="notes">{{ application['notes'] or '' }}</textarea>

                <br><br>

                <button class="btn" type="submit">
                    Update Application
                </button>

                <a class="btn"
                   href="/applications">
                    Cancel
                </a>

            </form>

        </div>

    </div>

    </body>
    </html>
    """, style=STYLE, navbar=NAVBAR,
       application=application)


# ---------------------------------------------------------
# DELETE APPLICATION
# ---------------------------------------------------------

@app.route("/delete-application/<int:application_id>")
def delete_application(application_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM applications
        WHERE id = ?
    """, (application_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("applications"))


# ---------------------------------------------------------
# PREPARATION
# ---------------------------------------------------------

@app.route("/preparation", methods=["GET", "POST"])
def preparation():

    conn = get_db()

    if request.method == "POST":

        task = request.form.get("task", "").strip()
        category = request.form.get("category", "").strip()

        if task:

            conn.execute("""
                INSERT INTO preparation
                (task, category, completed)
                VALUES (?, ?, 0)
            """, (task, category))

            conn.commit()

    tasks = conn.execute("""
        SELECT * FROM preparation
        ORDER BY id DESC
    """).fetchall()

    completed = sum(
        1 for task in tasks
        if task["completed"] == 1
    )

    progress = (
        int((completed / len(tasks)) * 100)
        if tasks else 0
    )

    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>

    <head>
        <title>Preparation</title>
        {{ style|safe }}
    </head>

    <body>

    {{ navbar|safe }}

    <div class="container">

        <div class="section">

            <h2>Placement Preparation</h2>

            <p class="subtitle">
                Track your preparation for technical and HR rounds.
            </p>

            <div class="progress">

                <div class="progress-bar"
                     style="width: {{ progress }}%;">
                    {{ progress }}%
                </div>

            </div>

        </div>


        <div class="section">

            <h3>Add Preparation Task</h3>

            <form method="POST">

                <label>Task</label>

                <input type="text"
                       name="task"
                       placeholder="Example: Complete SQL revision"
                       required>

                <label>Category</label>

                <select name="category">

                    <option>DSA</option>
                    <option>Python</option>
                    <option>Java</option>
                    <option>C</option>
                    <option>SQL</option>
                    <option>DBMS</option>
                    <option>Web Development</option>
                    <option>HR</option>
                    <option>Aptitude</option>

                </select>

                <br><br>

                <button class="btn" type="submit">
                    Add Task
                </button>

            </form>

        </div>


        <div class="section">

            <h3>Preparation Tasks</h3>

            {% if tasks %}

                {% for task in tasks %}

                <div class="task">

                    <a href="/toggle-task/{{ task['id'] }}">

                        <input type="checkbox"
                            {% if task['completed'] %}
                            checked
                            {% endif %}>

                    </a>

                    <div>

                        {% if task['completed'] %}

                        <span class="completed">
                            {{ task['task'] }}
                        </span>

                        {% else %}

                        {{ task['task'] }}

                        {% endif %}

                        <small>
                            — {{ task['category'] }}
                        </small>

                    </div>

                    <div style="margin-left:auto">

                        <a class="btn btn-danger btn-small"
                           href="/delete-task/{{ task['id'] }}">
                           Delete
                        </a>

                    </div>

                </div>

                {% endfor %}

            {% else %}

                <div class="empty">
                    No preparation tasks added.
                </div>

            {% endif %}

        </div>

    </div>

    </body>
    </html>
    """, style=STYLE, navbar=NAVBAR,
       tasks=tasks,
       progress=progress)


# ---------------------------------------------------------
# TOGGLE PREPARATION TASK
# ---------------------------------------------------------

@app.route("/toggle-task/<int:task_id>")
def toggle_task(task_id):

    conn = get_db()

    task = conn.execute("""
        SELECT completed FROM preparation
        WHERE id = ?
    """, (task_id,)).fetchone()

    if task:

        new_value = 0 if task["completed"] else 1

        conn.execute("""
            UPDATE preparation
            SET completed = ?
            WHERE id = ?
        """, (new_value, task_id))

        conn.commit()

    conn.close()

    return redirect(url_for("preparation"))


# ---------------------------------------------------------
# DELETE TASK
# ---------------------------------------------------------

@app.route("/delete-task/<int:task_id>")
def delete_task(task_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM preparation
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("preparation"))


# ---------------------------------------------------------
# COMPANY NOTES
# ---------------------------------------------------------

@app.route("/company-notes", methods=["GET", "POST"])
def company_notes():

    conn = get_db()

    if request.method == "POST":

        company = request.form.get("company", "").strip()
        topic = request.form.get("topic", "").strip()
        notes = request.form.get("notes", "").strip()

        if company and topic:

            conn.execute("""
                INSERT INTO company_notes
                (company, topic, notes)
                VALUES (?, ?, ?)
            """, (
                company,
                topic,
                notes
            ))

            conn.commit()

    notes = conn.execute("""
        SELECT * FROM company_notes
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>

    <head>
        <title>Company Notes</title>
        {{ style|safe }}
    </head>

    <body>

    {{ navbar|safe }}

    <div class="container">

        <div class="section">

            <h2>Company Preparation Notes</h2>

            <p class="subtitle">
                Store important information about companies,
                interview patterns and preparation topics.
            </p>

            <form method="POST">

                <div class="form-grid">

                    <div>

                        <label>Company</label>

                        <input type="text"
                               name="company"
                               placeholder="Example: TCS"
                               required>

                    </div>

                    <div>

                        <label>Topic</label>

                        <input type="text"
                               name="topic"
                               placeholder="Example: Technical Interview"
                               required>

                    </div>

                </div>

                <label>Notes</label>

                <textarea
                    name="notes"
                    placeholder="Write company-specific preparation notes..."></textarea>

                <br><br>

                <button class="btn" type="submit">
                    Save Company Note
                </button>

            </form>

        </div>


        <div class="section">

            <h3>Saved Company Notes</h3>

            {% if notes %}

                {% for note in notes %}

                <div class="note-card">

                    <h4>
                        {{ note["company"] }}
                    </h4>

                    <strong>
                        {{ note["topic"] }}
                    </strong>

                    <p>
                        {{ note["notes"] }}
                    </p>

                    <a class="btn btn-danger btn-small"
                       href="/delete-company-note/{{ note['id'] }}">
                       Delete
                    </a>

                </div>

                {% endfor %}

            {% else %}

                <div class="empty">
                    No company notes yet.
                </div>

            {% endif %}

        </div>

    </div>

    </body>
    </html>
    """, style=STYLE, navbar=NAVBAR,
       notes=notes)


# ---------------------------------------------------------
# DELETE COMPANY NOTE
# ---------------------------------------------------------

@app.route("/delete-company-note/<int:note_id>")
def delete_company_note(note_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM company_notes
        WHERE id = ?
    """, (note_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("company_notes"))


# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    init_db()

    print("----------------------------------------")
    print(" Student Placement Tracker")
    print("----------------------------------------")
    print("Server running at:")
    print("http://127.0.0.1:5000")
    print("----------------------------------------")

    app.run(debug=True)
