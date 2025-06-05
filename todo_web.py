from flask import Flask, render_template_string, request, redirect, url_for
import json
import os
from datetime import datetime

TASKS_FILE = "tasks.json"
DATE_FORMAT = "%Y-%m-%d"

# --- Data Logic (reuse from CLI) ---
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

def generate_task_id(tasks):
    if not tasks:
        return 1
    return max(task['id'] for task in tasks) + 1

def add_task(title, due, priority, category, note):
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
        "archived": False
    }
    tasks.append(task)
    save_tasks(tasks)

def update_task(task_id, title, due, priority, category, note):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = title
            task["due"] = due
            task["priority"] = priority
            task["category"] = category
            task["note"] = note
            break
    save_tasks(tasks)

def mark_done(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            break
    save_tasks(tasks)

def delete_task(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)

def archive_task(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["archived"] = True
            break
    save_tasks(tasks)

def unarchive_task(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["archived"] = False
            break
    save_tasks(tasks)

# --- Flask Web App ---
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>To-Do List Web</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background: #f0f0f0; }
        tr.done { text-decoration: line-through; color: #888; }
        .archived { background: #f9e6e6; }
        .actions form { display: inline; }
        .add-form { margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>To-Do List (Web)</h1>
    <form class="add-form" method="post" action="{{ url_for('add') }}">
        <input name="title" placeholder="Title" required>
        <input name="due" placeholder="Due (YYYY-MM-DD)">
        <select name="priority">
            <option value="low">Low</option>
            <option value="medium" selected>Medium</option>
            <option value="high">High</option>
        </select>
        <input name="category" placeholder="Category">
        <input name="note" placeholder="Note">
        <button type="submit">Add Task</button>
    </form>
    <table>
        <tr>
            <th>Title</th><th>Due</th><th>Priority</th><th>Category</th><th>Note</th>
            <th>Done</th><th>Archived</th><th>Actions</th>
        </tr>
        {% for task in tasks %}
        <tr class="{% if task.done %}done{% endif %} {% if task.archived %}archived{% endif %}">
            <td>{{ task.title }}</td>
            <td>{{ task.due }}</td>
            <td>{{ task.priority }}</td>
            <td>{{ task.category }}</td>
            <td>{{ task.note }}</td>
            <td>{{ "Yes" if task.done else "No" }}</td>
            <td>{{ "Yes" if task.archived else "No" }}</td>
            <td class="actions">
                {% if not task.done %}
                <form method="post" action="{{ url_for('mark_done_route', task_id=task.id) }}"><button>Done</button></form>
                {% endif %}
                <form method="post" action="{{ url_for('delete', task_id=task.id) }}"><button>Delete</button></form>
                {% if not task.archived %}
                <form method="post" action="{{ url_for('archive', task_id=task.id) }}"><button>Archive</button></form>
                {% else %}
                <form method="post" action="{{ url_for('unarchive', task_id=task.id) }}"><button>Unarchive</button></form>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    tasks = load_tasks()
    return render_template_string(HTML, tasks=tasks)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    due = request.form.get("due", "").strip() or "No due date"
    priority = request.form.get("priority", "medium")
    category = request.form.get("category", "General")
    note = request.form.get("note", "")
    if title:
        add_task(title, due, priority, category, note)
    return redirect(url_for("index"))

@app.route("/mark_done/<int:task_id>", methods=["POST"])
def mark_done_route(task_id):
    mark_done(task_id)
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    delete_task(task_id)
    return redirect(url_for("index"))

@app.route("/archive/<int:task_id>", methods=["POST"])
def archive(task_id):
    archive_task(task_id)
    return redirect(url_for("index"))

@app.route("/unarchive/<int:task_id>", methods=["POST"])
def unarchive(task_id):
    unarchive_task(task_id)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
