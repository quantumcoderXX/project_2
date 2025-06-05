from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime
import hashlib
from functools import wraps # Import wraps for decorator

TASKS_FILE = "tasks.json"
USERS_FILE = "users.json"
DATE_FORMAT = "%Y-%m-%d"
SECRET_KEY = "supersecretkey123"  # Change this in production

# --- Data Logic ---
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Handle cases where the JSON file might be empty or corrupted
        return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

def generate_task_id(tasks):
    if not tasks:
        return 1
    return max(task.get('id', 0) for task in tasks) + 1 # Use .get() for safety

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Handle cases where the JSON file might be empty or corrupted
        return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def find_user(username):
    users = load_users()
    for user in users:
        if user["username"] == username:
            return user
    return None

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
        if task.get("id") == task_id and task.get("username") == username:
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
        if task.get("id") == task_id and task.get("username") == username:
            task["done"] = True
            break
    save_tasks(tasks)

def delete_task(task_id, username):
    tasks = load_tasks()
    tasks = [t for t in tasks if not (t.get("id") == task_id and t.get("username") == username)]
    save_tasks(tasks)

def archive_task(task_id, username):
    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id and task.get("username") == username:
            task["archived"] = True
            break
    save_tasks(tasks)

def unarchive_task(task_id, username):
    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id and task.get("username") == username:
            task["archived"] = False
            break
    save_tasks(tasks)


# --- Flask Web App ---
app = Flask(__name__) # Fixed: __name__
app.secret_key = SECRET_KEY

# Decorator for login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- HTML Templates ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - To-Do List</title>
    <link href='https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap' rel='stylesheet'>
    <style>
        body { font-family: 'Roboto', Arial, sans-serif; background: linear-gradient(120deg, #f6d365 0%, #fda085 100%); min-height: 100vh; margin: 0; display: flex; align-items: center; justify-content: center;}
        .login-container { max-width: 400px; width: 90%; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 32px 40px 24px 40px; }
        h2 { text-align: center; color: #f76b1c; margin-bottom: 32px; font-weight: 700; letter-spacing: 2px; }
        form { display: flex; flex-direction: column; gap: 16px; }
        input { padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; outline: none; transition: border 0.2s; }
        input:focus { border: 1.5px solid #f76b1c; }
        button { background: linear-gradient(90deg, #f76b1c 0%, #fad961 100%); color: #fff; border: none; border-radius: 6px; padding: 10px 0; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background 0.2s; }
        button:hover { background: linear-gradient(90deg, #fad961 0%, #f76b1c 100%); }
        .switch-link { text-align: center; margin-top: 10px; }
        .switch-link a { color: #f76b1c; text-decoration: underline; font-size: 0.98rem; }
        .flash { padding: 10px; margin-bottom: 10px; border-radius: 5px; text-align: center; }
        .flash.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .flash.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        {% for category, message in messages %}
        <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
        {% endif %}
        {% endwith %}
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
        body { font-family: 'Roboto', Arial, sans-serif; background: linear-gradient(120deg, #f6d365 0%, #fda085 100%); min-height: 100vh; margin: 0; display: flex; align-items: center; justify-content: center;}
        .login-container { max-width: 400px; width: 90%; margin: 80px auto; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 32px 40px 24px 40px; }
        h2 { text-align: center; color: #f76b1c; margin-bottom: 32px; font-weight: 700; letter-spacing: 2px; }
        form { display: flex; flex-direction: column; gap: 16px; }
        input { padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; outline: none; transition: border 0.2s; }
        input:focus { border: 1.5px solid #f76b1c; }
        button { background: linear-gradient(90deg, #f76b1c 0%, #fad961 100%); color: #fff; border: none; border-radius: 6px; padding: 10px 0; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background 0.2s; }
        button:hover { background: linear-gradient(90deg, #fad961 0%, #f76b1c 100%); }
        .switch-link { text-align: center; margin-top: 10px; }
        .switch-link a { color: #f76b1c; text-decoration: underline; font-size: 0.98rem; }
        .flash { padding: 10px; margin-bottom: 10px; border-radius: 5px; text-align: center; }
        .flash.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .flash.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Register</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        {% for category, message in messages %}
        <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
        {% endif %}
        {% endwith %}
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

# Main task list HTML (Combined and cleaned up)
MAIN_HTML = """
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
        .task-title-link {
            text-decoration: none;
            color: inherit;
        }
        .task-title-link:hover {
            text-decoration: underline;
        }
        .flash { padding: 10px; margin-bottom: 10px; border-radius: 5px; text-align: center; }
        .flash.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .flash.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }

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

    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
    {% for category, message in messages %}
    <div class="flash {{ category }}">{{ message }}</div>
    {% endfor %}
    {% endif %}
    {% endwith %}

    <form class="add-form" method="post" action="{{ url_for('add') }}">
        <input name="title" placeholder="Title" required value="{{ edit_task.title if edit_task else '' }}">
        <input name="due" type="date" placeholder="Due (YYYY-MM-DD)" value="{{ edit_task.due if edit_task and edit_task.due != 'No due date' else '' }}">
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
            <td><a href="{{ url_for('edit', task_id=task.id) }}" class="task-title-link">{{ task.title }}</a></td>
            <td>{{ task.due }}</td>
            <td>{{ task.priority }}</td>
            <td>{{ task.category }}</td>
            <td>{{ task.note }}</td>
            <td>{{ task.created }}</td>
            <td>{{ "Yes" if task.done else "No" }}</td>
            <td>{{ "Yes" if task.archived else "No" }}</td>
            <td class="actions">
                <form method="get" action="{{ url_for('edit', task_id=task.id) }}"><button type="submit" title="Edit"><i class="fa-solid fa-pen"></i></button></form>
                {% if not task.done %}
                <form method="post" action="{{ url_for('mark_done_route', task_id=task.id) }}"><button type="submit" title="Mark as Done"><i class="fa-solid fa-check"></i></button></form>
                {% endif %}
                <form method="post" action="{{ url_for('delete', task_id=task.id) }}"><button type="submit" title="Delete"><i class="fa-solid fa-trash"></i></button></form>
                {% if not task.archived %}
                <form method="post" action="{{ url_for('archive', task_id=task.id) }}"><button type="submit" title="Archive"><i class="fa-solid fa-box-archive"></i></button></form>
                {% else %}
                <form method="post" action="{{ url_for('unarchive', task_id=task.id) }}"><button type="submit" title="Unarchive"><i class="fa-solid fa-box-open"></i></button></form>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    </div>
</body>
</html>
"""

# --- Flask Routes ---
@app.route("/", methods=["GET"])
@login_required
def index():
    q = request.args.get("q", "").strip().lower()
    username = session['username']
    
    all_tasks = load_tasks()
    user_tasks = [t for t in all_tasks if t.get('username') == username]

    # Sort tasks by due date
    def parse_due(task):
        try:
            return datetime.strptime(task["due"], DATE_FORMAT)
        except ValueError:
            return datetime.max # Tasks with invalid/no due date go to the end

    user_tasks = sorted(user_tasks, key=parse_due)

    # Apply search filter
    if q:
        user_tasks = [
            t for t in user_tasks
            if q in t["title"].lower() or
               q in t.get("category", "").lower() or
               q in t.get("note", "").lower()
        ]
    
    # Initialize edit_task as None for the main view
    return render_template_string(MAIN_HTML, tasks=user_tasks, q=q, edit_task=None, session=session)


@app.route("/add", methods=["POST"])
@login_required
def add():
    edit_id = request.form.get("edit_id")
    title = request.form.get("title", "").strip()
    due = request.form.get("due", "").strip()
    priority = request.form.get("priority", "medium")
    category = request.form.get("category", "General")
    note = request.form.get("note", "")
    username = session['username']

    # Validate due date format if provided
    if due:
        try:
            datetime.strptime(due, DATE_FORMAT)
        except ValueError:
            flash(f"Invalid due date format. Please use {DATE_FORMAT}.", 'error')
            # Redirect back to index with pre-filled form values for correction
            # This is a bit complex without redirecting to a separate edit page
            # For simplicity, I'll clear it or leave as is. User needs to re-enter.
            due = "No due date" # Reset to default if invalid
    else:
        due = "No due date" # Default for empty due date

    if not title:
        flash("Task title cannot be empty.", 'error')
    else:
        if edit_id:
            update_task(int(edit_id), title, due, priority, category, note, username)
            flash("Task updated successfully!", 'success')
        else:
            add_task(title, due, priority, category, note, username)
            flash("Task added successfully!", 'success')
            
    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>", methods=["GET"])
@login_required
def edit(task_id):
    username = session['username']
    all_tasks = load_tasks()
    user_tasks = [t for t in all_tasks if t.get('username') == username]
    
    # Find the task to edit
    edit_task = next((t for t in user_tasks if t["id"] == task_id), None)

    if not edit_task:
        flash("Task not found or you don't have permission to edit it.", 'error')
        return redirect(url_for('index'))

    # Sort and filter tasks for display on the main page (same logic as index)
    q = request.args.get("q", "").strip().lower()
    def parse_due(task):
        try:
            return datetime.strptime(task["due"], DATE_FORMAT)
        except ValueError:
            return datetime.max
    tasks_for_display = sorted(user_tasks, key=parse_due)
    
    if q:
        tasks_for_display = [
            t for t in tasks_for_display
            if q in t["title"].lower() or
               q in t.get("category", "").lower() or
               q in t.get("note", "").lower()
        ]

    return render_template_string(MAIN_HTML, tasks=tasks_for_display, q=q, edit_task=edit_task, session=session)


@app.route("/mark_done/<int:task_id>", methods=["POST"])
@login_required
def mark_done_route(task_id):
    username = session['username']
    mark_done(task_id, username)
    flash("Task marked as done!", 'success')
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete(task_id):
    username = session['username']
    delete_task(task_id, username)
    flash("Task deleted successfully!", 'success')
    return redirect(url_for("index"))

@app.route("/archive/<int:task_id>", methods=["POST"])
@login_required
def archive(task_id):
    username = session['username']
    archive_task(task_id, username)
    flash("Task archived!", 'success')
    return redirect(url_for("index"))

@app.route("/unarchive/<int:task_id>", methods=["POST"])
@login_required
def unarchive(task_id):
    username = session['username']
    unarchive_task(task_id, username)
    flash("Task unarchived!", 'success')
    return redirect(url_for("index"))


# --- Authentication Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if 'username' in session:
        return redirect(url_for('index')) # Already logged in
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = find_user(username)
        if user and user["password"] == hash_password(password):
            session['username'] = username
            flash(f"Welcome back, {username}!", 'success')
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", 'error')
    
    return render_template_string(LOGIN_HTML)

@app.route("/register", methods=["GET", "POST"])
def register():
    if 'username' in session:
        return redirect(url_for('index')) # Already logged in

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        
        if not username or not password:
            flash("Username and password are required.", 'error')
        elif find_user(username):
            flash("Username already exists. Please choose a different one.", 'error')
        elif password != confirm:
            flash("Passwords do not match.", 'error')
        else:
            users = load_users()
            users.append({"username": username, "password": hash_password(password)})
            save_users(users)
            flash("Registration successful! Please log in.", 'success')
            return redirect(url_for('login'))
            
    return render_template_string(REGISTER_HTML)

@app.route("/logout")
@login_required # Ensure only logged-in users can logout
def logout():
    session.pop('username', None)
    flash("You have been logged out.", 'success')
    return redirect(url_for('login'))

if __name__ == "__main__": # Fixed: __name__
    app.run(debug=True)
