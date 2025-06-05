from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime

import hashlib


TASKS_FILE = "tasks.json"
USERS_FILE = "users.json"
DATE_FORMAT = "%Y-%m-%d"
SECRET_KEY = "supersecretkey123"  # Change this in production

# --- Data Logic (reuse from CLI) ---
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)
# --- Data Logic (reuse from CLI) ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def find_user(username):
    users = load_users()
    for user in users:
        if user["username"] == username:
            return user
    return None

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

def generate_task_id(tasks):
    if not tasks:
        return 1
    return max(task['id'] for task in tasks) + 1

def add_task(title, due, priority, category, note, username):
    tasks = load_tasks()
    task = {
        "id": generate_task_id(tasks),
        "title": title,
        "due": due,
        "priority": priority,
        "category": category or "General",
        "note": note or "",
        "done": False,
        "created": datetime.now().strftime(DATE_FORMAT),
        "archived": False,
        "username": username
    }
    tasks.append(task)
    save_tasks(tasks)

def update_task(task_id, title, due, priority, category, note, username):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id and task["username"] == username:
            task["title"] = title
            task["due"] = due
            task["priority"] = priority
            task["category"] = category
            task["note"] = note
            break
    save_tasks(tasks)

def mark_done(task_id, username):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id and task["username"] == username:
            task["done"] = True
            break
    save_tasks(tasks)

def delete_task(task_id, username):
    tasks = load_tasks()
    tasks = [t for t in tasks if not (t["id"] == task_id and t["username"] == username)]
    save_tasks(tasks)

def archive_task(task_id, username):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id and task["username"] == username:
            task["archived"] = True
            break
    save_tasks(tasks)

def unarchive_task(task_id, username):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id and task["username"] == username:
            task["archived"] = False
            break
    save_tasks(tasks)


# --- Flask Web App ---
app = Flask(_name_)
app.secret_key = SECRET_KEY

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - To-Do List</title>
    <link href='https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap' rel='stylesheet'>
    <style>
        body { font-family: 'Roboto', Arial, sans-serif; background: linear-gradient(120deg, #f6d365 0%, #fda085 100%); min-height: 100vh; margin: 0; }
        .login-container { max-width: 400px; margin: 80px auto; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 32px 40px 24px 40px; }
        h2 { text-align: center; color: #f76b1c; margin-bottom: 32px; font-weight: 700; letter-spacing: 2px; }
        form { display: flex; flex-direction: column; gap: 16px; }
        input { padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; outline: none; transition: border 0.2s; }
        input:focus { border: 1.5px solid #f76b1c; }
        button { background: linear-gradient(90deg, #f76b1c 0%, #fad961 100%); color: #fff; border: none; border-radius: 6px; padding: 10px 0; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background 0.2s; }
        button:hover { background: linear-gradient(90deg, #fad961 0%, #f76b1c 100%); }
        .switch-link { text-align: center; margin-top: 10px; }
        .switch-link a { color: #f76b1c; text-decoration: underline; font-size: 0.98rem; }
        .error { color: #d32f2f; text-align: center; margin-bottom: 10px; }
        .success { color: #388e3c; text-align: center; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if success %}<div class="success">{{ success }}</div>{% endif %}
        <form method="post">
            <input name="username" placeholder="Username" required autofocus>
            <input name="password" type="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="switch-link">Don't have an account? <a href="{{ url_for('register') }}">Register</a></div>
    </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Register - To-Do List</title>
    <link href='https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap' rel='stylesheet'>
    <style>
        body { font-family: 'Roboto', Arial, sans-serif; background: linear-gradient(120deg, #f6d365 0%, #fda085 100%); min-height: 100vh; margin: 0; }
        .login-container { max-width: 400px; margin: 80px auto; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 32px 40px 24px 40px; }
        h2 { text-align: center; color: #f76b1c; margin-bottom: 32px; font-weight: 700; letter-spacing: 2px; }
        form { display: flex; flex-direction: column; gap: 16px; }
        input { padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; outline: none; transition: border 0.2s; }
        input:focus { border: 1.5px solid #f76b1c; }
        button { background: linear-gradient(90deg, #f76b1c 0%, #fad961 100%); color: #fff; border: none; border-radius: 6px; padding: 10px 0; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background 0.2s; }
        button:hover { background: linear-gradient(90deg, #fad961 0%, #f76b1c 100%); }
        .switch-link { text-align: center; margin-top: 10px; }
        .switch-link a { color: #f76b1c; text-decoration: underline; font-size: 0.98rem; }
        .error { color: #d32f2f; text-align: center; margin-bottom: 10px; }
        .success { color: #388e3c; text-align: center; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Register</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if success %}<div class="success">{{ success }}</div>{% endif %}
        <form method="post">
            <input name="username" placeholder="Username" required autofocus>
            <input name="password" type="password" placeholder="Password" required>
            <input name="confirm" type="password" placeholder="Confirm Password" required>
            <button type="submit">Register</button>
        </form>
        <div class="switch-link">Already have an account? <a href="{{ url_for('login') }}">Login</a></div>
    </div>
</body>
</html>
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>To-Do List Web</title>
    <link href="https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <style>
        body {
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            background: linear-gradient(120deg, #f6d365 0%, #fda085 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            margin: 40px auto;
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            padding: 32px 40px 24px 40px;
        }
        h1 {
            text-align: center;
            color: #f76b1c;
            margin-bottom: 32px;
            font-weight: 700;
            letter-spacing: 2px;
        }
        .add-form {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 28px;
            justify-content: center;
        }
        .add-form input, .add-form select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 1rem;
            outline: none;
            transition: border 0.2s;
        }
        .add-form input:focus, .add-form select:focus {
            border: 1.5px solid #f76b1c;
        }
        .add-form button {
            background: linear-gradient(90deg, #f76b1c 0%, #fad961 100%);
            color: #fff;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(247,107,28,0.08);
            transition: background 0.2s;
        }
        .add-form button:hover {
            background: linear-gradient(90deg, #fad961 0%, #f76b1c 100%);
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
            background: #fff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        th, td {
            border: none;
            padding: 12px 10px;
            text-align: left;
        }
        th {
            background: #f76b1c;
            color: #fff;
            font-weight: 700;
            letter-spacing: 1px;
        }
        tr.done td {
            text-decoration: line-through;
            color: #aaa;
            background: #f7f7f7;
        }
        tr.archived td {
            background: #ffe3e3;
        }
        .actions form {
            display: inline;
        }
        .actions button {
            background: none;
            border: none;
            color: #f76b1c;
            font-size: 1.1rem;
            margin: 0 2px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            transition: background 0.15s;
        }
        .actions button:hover {
            background: #f6d36533;
        }
        @media (max-width: 700px) {
            .container { padding: 10px; }
            .add-form { flex-direction: column; align-items: stretch; }
            table, th, td { font-size: 0.95rem; }
        }
    </style>
</head>
<body>
    <div class="container">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <h1 style="margin-bottom:0;"><i class="fa-solid fa-list-check"></i> To-Do List</h1>
        <div style="font-size:1.1rem;">
            <span style="color:#f76b1c;font-weight:600;">{{ session['username'] }}</span>
            <a href="{{ url_for('logout') }}" style="margin-left:18px;color:#f76b1c;text-decoration:underline;font-size:0.98rem;">Logout</a>
        </div>
    </div>
    <form class="add-form" method="post" action="{{ url_for('add') }}">
        <input name="title" placeholder="Title" required value="{{ edit_task.title if edit_task else '' }}">
        <input name="due" placeholder="Due (YYYY-MM-DD)" value="{{ edit_task.due if edit_task else '' }}">
        <select name="priority">
            <option value="low" {% if edit_task and edit_task.priority=='low' %}selected{% endif %}>Low</option>
            <option value="medium" {% if not edit_task or edit_task.priority=='medium' %}selected{% endif %}>Medium</option>
            <option value="high" {% if edit_task and edit_task.priority=='high' %}selected{% endif %}>High</option>
        </select>
        <input name="category" placeholder="Category" value="{{ edit_task.category if edit_task else '' }}">
        <input name="note" placeholder="Note" value="{{ edit_task.note if edit_task else '' }}">
        {% if edit_task %}
        <input type="hidden" name="edit_id" value="{{ edit_task.id }}">
        <button type="submit"><i class="fa-solid fa-pen-to-square"></i> Update Task</button>
        <a href="{{ url_for('index') }}" style="align-self:center;color:#f76b1c;text-decoration:underline;font-size:0.95rem;margin-left:8px;">Cancel</a>
        {% else %}
        <button type="submit"><i class="fa-solid fa-plus"></i> Add Task</button>
        {% endif %}
    </form>
    <form method="get" style="margin-bottom:18px;display:flex;gap:10px;justify-content:center;">
        <input name="q" placeholder="Search by title, category, or note" value="{{ q|default('') }}" style="padding:7px 12px;border-radius:6px;border:1px solid #ddd;width:260px;">
        <button type="submit" style="background:#f76b1c;color:#fff;border:none;border-radius:6px;padding:7px 18px;font-weight:600;cursor:pointer;"><i class="fa-solid fa-magnifying-glass"></i> Search</button>
        {% if q %}<a href="{{ url_for('index') }}" style="align-self:center;color:#f76b1c;text-decoration:underline;font-size:0.95rem;">Clear</a>{% endif %}
    </form>
    <table>
        <tr>
            <th>Title</th><th>Due</th><th>Priority</th><th>Category</th><th>Note</th><th>Created</th>
            <th>Done</th><th>Archived</th><th>Actions</th>
        </tr>
        {% for task in tasks %}
        <tr class="{% if task.done %}done{% endif %} {% if task.archived %}archived{% endif %}">
            <td>{{ task.title }}</td>
            <td>{{ task.due }}</td>
            <td>{{ task.priority }}</td>
            <td>{{ task.category }}</td>
            <td>{{ task.note }}</td>
            <td>{{ task.created }}</td>
            <td>{{ "Yes" if task.done else "No" }}</td>
            <td>{{ "Yes" if task.archived else "No" }}</td>
            <td class="actions">
                <form method="get" action="{{ url_for('edit', task_id=task.id) }}"><button title="Edit"><i class="fa-solid fa-pen"></i></button></form>
                {% if not task.done %}
                <form method="post" action="{{ url_for('mark_done_route', task_id=task.id) }}"><button title="Mark as Done"><i class="fa-solid fa-check"></i></button></form>
                {% endif %}
                <form method="post" action="{{ url_for('delete', task_id=task.id) }}"><button title="Delete"><i class="fa-solid fa-trash"></i></button></form>
                {% if not task.archived %}
                <form method="post" action="{{ url_for('archive', task_id=task.id) }}"><button title="Archive"><i class="fa-solid fa-box-archive"></i></button></form>
                {% else %}
                <form method="post" action="{{ url_for('unarchive', task_id=task.id) }}"><button title="Unarchive"><i class="fa-solid fa-box-open"></i></button></form>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    </div>
</body>
</html>
"""


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
@login_required
def index():
    q = request.args.get("q", "").strip().lower()
    username = session['username']
    tasks = [t for t in load_tasks() if t.get('username') == username]
    def parse_due(task):
        try:
            return datetime.strptime(task["due"], "%Y-%m-%d")
        except Exception:
            return datetime.max
    tasks = sorted(tasks, key=parse_due)
    if q:
        tasks = [t for t in tasks if q in t["title"].lower() or q in t.get("category", "").lower() or q in t.get("note", "").lower()]
    return render_template_string(HTML, tasks=tasks, q=q, edit_task=None, session=session)

@app.route("/add", methods=["POST"])
@login_required
def add():
    edit_id = request.form.get("edit_id")
    title = request.form.get("title", "").strip()
    due = request.form.get("due", "").strip() or "No due date"
    priority = request.form.get("priority", "medium")
    category = request.form.get("category", "General")
    note = request.form.get("note", "")
    username = session['username']
    if title:
        if edit_id:
            update_task(int(edit_id), title, due, priority, category, note, username)
        else:
            add_task(title, due, priority, category, note, username)
    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>", methods=["GET"])
@login_required
def edit(task_id):
    q = request.args.get("q", "")
    username = session['username']
    tasks = [t for t in load_tasks() if t.get('username') == username]
    edit_task = next((t for t in tasks if t["id"] == task_id), None)
    def parse_due(task):
        try:
            return datetime.strptime(task["due"], "%Y-%m-%d")
        except Exception:
            return datetime.max
    tasks = sorted(tasks, key=parse_due)
    if q:
        tasks = [t for t in tasks if q in t["title"].lower() or q in t.get("category", "").lower() or q in t.get("note", "").lower()]
    return render_template_string(HTML, tasks=tasks, q=q, edit_task=edit_task, session=session)

@app.route("/mark_done/<int:task_id>", methods=["POST"])
@login_required
def mark_done_route(task_id):
    username = session['username']
    mark_done(task_id, username)
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete(task_id):
    username = session['username']
    delete_task(task_id, username)
    return redirect(url_for("index"))

@app.route("/archive/<int:task_id>", methods=["POST"])
@login_required
def archive(task_id):
    username = session['username']
    archive_task(task_id, username)
    return redirect(url_for("index"))

@app.route("/unarchive/<int:task_id>", methods=["POST"])
@login_required
def unarchive(task_id):
    username = session['username']
    unarchive_task(task_id, username)
    return redirect(url_for("index"))


# --- Authentication Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    success = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = find_user(username)
        if user and user["password"] == hash_password(password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password."
    if 'registered' in request.args:
        success = "Registration successful! Please log in."
    return render_template_string(LOGIN_HTML, error=error, success=success)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not username or not password:
            error = "Username and password are required."
        elif find_user(username):
            error = "Username already exists."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            users = load_users()
            users.append({"username": username, "password": hash_password(password)})
            save_users(users)
            return redirect(url_for('login', registered=1))
    return render_template_string(REGISTER_HTML, error=error, success=success)

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if _name_ == "_main_":
    app.run(debug=True)
