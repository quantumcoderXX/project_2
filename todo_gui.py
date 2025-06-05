import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

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

# --- GUI ---
class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List GUI")
        self.create_widgets()
        self.refresh_tasks()

    def create_widgets(self):
        # Entry frame
        entry_frame = ttk.LabelFrame(self.root, text="Add/Edit Task")
        entry_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(entry_frame, text="Title:").grid(row=0, column=0, sticky="e")
        self.title_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.title_var, width=30).grid(row=0, column=1, padx=2)

        ttk.Label(entry_frame, text="Due (YYYY-MM-DD):").grid(row=0, column=2, sticky="e")
        self.due_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.due_var, width=15).grid(row=0, column=3, padx=2)

        ttk.Label(entry_frame, text="Priority:").grid(row=1, column=0, sticky="e")
        self.priority_var = tk.StringVar(value="medium")
        ttk.Combobox(entry_frame, textvariable=self.priority_var, values=["low", "medium", "high"], width=12).grid(row=1, column=1, padx=2)

        ttk.Label(entry_frame, text="Category:").grid(row=1, column=2, sticky="e")
        self.category_var = tk.StringVar(value="General")
        ttk.Entry(entry_frame, textvariable=self.category_var, width=15).grid(row=1, column=3, padx=2)

        ttk.Label(entry_frame, text="Note:").grid(row=2, column=0, sticky="e")
        self.note_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.note_var, width=50).grid(row=2, column=1, columnspan=3, padx=2, pady=2, sticky="ew")

        self.add_btn = ttk.Button(entry_frame, text="Add Task", command=self.add_task)
        self.add_btn.grid(row=3, column=1, pady=4)
        self.update_btn = ttk.Button(entry_frame, text="Update Task", command=self.update_task, state="disabled")
        self.update_btn.grid(row=3, column=2, pady=4)

        # Task list
        self.tree = ttk.Treeview(self.root, columns=("id", "title", "due", "priority", "category", "done", "archived"), show="headings")
        for col in ("id", "title", "due", "priority", "category", "done", "archived"):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=80 if col=="title" else 60)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", self.on_tree_select)

        # Action buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Mark Done", command=self.mark_done).pack(side="left")
        ttk.Button(btn_frame, text="Delete", command=self.delete_task).pack(side="left")
        ttk.Button(btn_frame, text="Archive", command=self.archive_task).pack(side="left")
        ttk.Button(btn_frame, text="Unarchive", command=self.unarchive_task).pack(side="left")
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_tasks).pack(side="right")

    def add_task(self):
        title = self.title_var.get().strip()
        due = self.due_var.get().strip() or "No due date"
        priority = self.priority_var.get().strip() or "medium"
        category = self.category_var.get().strip() or "General"
        note = self.note_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Title is required.")
            return
        add_task(title, due, priority, category, note)
        self.clear_entry()
        self.refresh_tasks()

    def update_task(self):
        if not hasattr(self, "selected_id"):
            return
        title = self.title_var.get().strip()
        due = self.due_var.get().strip() or "No due date"
        priority = self.priority_var.get().strip() or "medium"
        category = self.category_var.get().strip() or "General"
        note = self.note_var.get().strip()
        update_task(self.selected_id, title, due, priority, category, note)
        self.clear_entry()
        self.refresh_tasks()
        self.add_btn["state"] = "normal"
        self.update_btn["state"] = "disabled"

    def mark_done(self):
        sel = self.tree.selection()
        if not sel:
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        mark_done(task_id)
        self.refresh_tasks()

    def delete_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        if messagebox.askyesno("Delete", "Delete this task?"):
            delete_task(task_id)
            self.refresh_tasks()

    def archive_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        archive_task(task_id)
        self.refresh_tasks()

    def unarchive_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        unarchive_task(task_id)
        self.refresh_tasks()

    def refresh_tasks(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for task in load_tasks():
            self.tree.insert("", "end", values=(task["id"], task["title"], task["due"], task["priority"], task["category"], "Yes" if task["done"] else "No", "Yes" if task.get("archived", False) else "No"))

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        vals = item["values"]
        self.selected_id = int(vals[0])
        self.title_var.set(vals[1])
        self.due_var.set(vals[2])
        self.priority_var.set(vals[3])
        self.category_var.set(vals[4])
        # Note is not shown in the table, so fetch from data
        for task in load_tasks():
            if task["id"] == self.selected_id:
                self.note_var.set(task.get("note", ""))
                break
        self.add_btn["state"] = "disabled"
        self.update_btn["state"] = "normal"

    def clear_entry(self):
        self.title_var.set("")
        self.due_var.set("")
        self.priority_var.set("medium")
        self.category_var.set("General")
        self.note_var.set("")
        self.add_btn["state"] = "normal"
        self.update_btn["state"] = "disabled"
        if hasattr(self, "selected_id"):
            del self.selected_id

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
