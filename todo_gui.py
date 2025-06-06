import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import json
import os
import csv

TASKS_FILE = "tasks.json"
DATE_FORMAT = "%Y-%m-%d"

# --- Data Logic ---
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Could not read tasks.json. File might be corrupted.")
        return []

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
        self.create_menu() # Call to create the menu
        self.create_widgets()
        self.refresh_tasks()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_info)

    def show_about_info(self):
        """Displays information about the application and its contributors."""
        about_text = (
            "To-Do List GUI Application\n"
            "Version: 1.0\n"
            "Developed by: Your Name/Organization\n\n"
            "Special thanks to:\n"
            "- [Contributor Name 1] for [specific contribution, e.g., UI design tips]\n"
            "- [Contributor Name 2] for [specific contribution, e.g., testing assistance]\n\n"
            "This application helps you manage your daily tasks efficiently."
        )
        messagebox.showinfo("About To-Do List", about_text)


    def create_widgets(self):
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

        # Filter frame
        filter_frame = ttk.LabelFrame(self.root, text="Filter Tasks")
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Filter by Category:").pack(side="left", padx=5)
        self.filter_category_var = tk.StringVar(value="All Categories")
        self.category_filter_combobox = ttk.Combobox(filter_frame, textvariable=self.filter_category_var, width=20, state="readonly")
        self.category_filter_combobox.pack(side="left", padx=5)
        self.category_filter_combobox.bind("<<ComboboxSelected>>", self.refresh_tasks)
        self.populate_category_filter()

        self.tree = ttk.Treeview(self.root, columns=("id", "title", "due", "priority", "category", "done", "archived"), show="headings")
        for col in ("id", "title", "due", "priority", "category", "done", "archived"):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=80 if col=="title" else 60, anchor="center")
        self.tree.column("title", width=150, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", self.on_tree_select)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Mark Done", command=self.mark_done).pack(side="left")
        ttk.Button(btn_frame, text="Delete", command=self.delete_task).pack(side="left")
        ttk.Button(btn_frame, text="Archive", command=self.archive_task).pack(side="left")
        ttk.Button(btn_frame, text="Unarchive", command=self.unarchive_task).pack(side="left")
        ttk.Button(btn_frame, text="Export to CSV", command=self.export_to_csv).pack(side="left", padx=(15, 0))
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_tasks).pack(side="right")

    def populate_category_filter(self):
        tasks = load_tasks()
        categories = sorted(list(set(task["category"] for task in tasks if "category" in task)))
        self.category_filter_combobox["values"] = ["All Categories"] + categories

    def add_task(self):
        title = self.title_var.get().strip()
        due = self.due_var.get().strip()
        priority = self.priority_var.get().strip()
        category = self.category_var.get().strip()
        note = self.note_var.get().strip()

        if not title:
            messagebox.showerror("Error", "Title is required.")
            return

        if due and due != "No due date":
            try:
                datetime.strptime(due, DATE_FORMAT)
            except ValueError:
                messagebox.showerror("Invalid Date", f"Due date must be in {DATE_FORMAT} format. Leaving blank will set 'No due date'.")
                return

        add_task(title, due, priority, category, note)
        self.clear_entry()
        self.populate_category_filter()
        self.refresh_tasks()

    def update_task(self):
        if not hasattr(self, "selected_id"):
            messagebox.showwarning("No Selection", "Please select a task to update.")
            return

        title = self.title_var.get().strip()
        due = self.due_var.get().strip()
        priority = self.priority_var.get().strip()
        category = self.category_var.get().strip()
        note = self.note_var.get().strip()

        if not title:
            messagebox.showerror("Error", "Title is required.")
            return

        if due and due != "No due date":
            try:
                datetime.strptime(due, DATE_FORMAT)
            except ValueError:
                messagebox.showerror("Invalid Date", f"Due date must be in {DATE_FORMAT} format. Leaving blank will set 'No due date'.")
                return

        update_task(self.selected_id, title, due, priority, category, note)
        self.clear_entry()
        self.populate_category_filter()
        self.refresh_tasks()
        self.add_btn["state"] = "normal"
        self.update_btn["state"] = "disabled"

    def mark_done(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a task to mark as done.")
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        mark_done(task_id)
        self.refresh_tasks()

    def delete_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a task to delete.")
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        if messagebox.askyesno("Delete", "Are you sure you want to delete this task permanently?"):
            delete_task(task_id)
            self.populate_category_filter()
            self.refresh_tasks()
            self.clear_entry()

    def archive_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a task to archive.")
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        archive_task(task_id)
        self.refresh_tasks()

    def unarchive_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a task to unarchive.")
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        unarchive_task(task_id)
        self.refresh_tasks()

    def export_to_csv(self):
        tasks = load_tasks()
        if not tasks:
            messagebox.showinfo("Export", "No tasks to export.")
            return

        default_filename = f"tasks_{datetime.now().strftime('%Y%m%d')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Save tasks as CSV"
        )
        if not file_path:
            return

        try:
            fieldnames = ["id", "title", "due", "priority", "category", "note", "done", "created", "archived"]
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for task in tasks:
                    row = {field: task.get(field, "") for field in fieldnames}
                    writer.writerow(row)
            messagebox.showinfo("Export Success", f"Tasks exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export tasks: {e}")

    def refresh_tasks(self, event=None):
        for row in self.tree.get_children():
            self.tree.delete(row)

        selected_category = self.filter_category_var.get()
        all_tasks = load_tasks()

        filtered_tasks = [task for task in all_tasks if selected_category == "All Categories" or task.get("category") == selected_category]

        for task in filtered_tasks:
            self.tree.insert("", "end", values=(
                task["id"],
                task["title"],
                task["due"],
                task["priority"],
                task["category"],
                "Yes" if task["done"] else "No",
                "Yes" if task.get("archived", False) else "No"
            ))

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
