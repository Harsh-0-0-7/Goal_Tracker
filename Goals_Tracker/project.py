import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------- Data Handling ----------------------------
class GoalTracker:
    def __init__(self, file_path="goals.json"):
        self.file_path = file_path
        self.data = self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                # Handle legacy data format
                if "goals" in data and "active_goals" not in data:
                    data["active_goals"] = data.pop("goals")
                # Initialize required keys
                data.setdefault("active_goals", [])
                data.setdefault("completed_goals", [])
                # Ensure all goals have required fields
                for goal in data["active_goals"]:
                    goal.setdefault("unit", "units")
                    goal.setdefault("missed_days", [])
                    goal.setdefault("daily_logs", [])
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {"active_goals": [], "completed_goals": []}

    def save_data(self):
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_goal(self, name, total_target, weekly_target, unit):
        self.data["active_goals"].append({
            "name": name,
            "total_target": float(total_target),
            "weekly_target": float(weekly_target),
            "unit": unit,
            "daily_logs": [],
        })
        self.save_data()

    def delete_goal(self, goal_name):
        self.data["active_goals"] = [g for g in self.data["active_goals"] if g["name"] != goal_name]
        self.save_data()

    def complete_goal(self, goal):
        goal["completion_date"] = datetime.now().strftime("%Y-%m-%d")
        self.data["completed_goals"].append(goal)
        self.data["active_goals"].remove(goal)
        self.save_data()

    def log_progress(self, goal_name, progress):
        today = datetime.now().strftime("%Y-%m-%d")
        for goal in self.data["active_goals"]:
            if goal["name"] == goal_name:
                
                # Add progress
                goal["daily_logs"].append({
                    "date": today,
                    "progress": float(progress)
                })
                
                # Check for goal completion
                total_progress = sum(log["progress"] for log in goal["daily_logs"])
                if total_progress >= goal["total_target"]:
                    self.complete_goal(goal)
                self.save_data()
                return True
        return False

    def log_missed_day(self, goal_name, reason):
        today = datetime.now().strftime("%Y-%m-%d")
        for goal in self.data["active_goals"]:
            if goal["name"] == goal_name:
                goal["missed_days"].append({
                    "date": today,
                    "reason": reason
                })
                self.save_data()
                return True
        return False

    def get_weekly_progress(self, goal_name):
        current_week = datetime.now().isocalendar()[1]
        for goal in self.data["active_goals"]:
            if goal["name"] == goal_name:
                return sum(
                    log["progress"] for log in goal["daily_logs"]
                    if datetime.strptime(log["date"], "%Y-%m-%d").isocalendar()[1] == current_week
                )
        return 0

# ---------------------------- GUI Application ----------------------------
class GoalTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Goal Tracker")
        self.tracker = GoalTracker()
        self.setup_ui()
        self.update_goal_dropdown()

    def setup_ui(self):
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 12))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.active_tab = ttk.Frame(self.notebook)
        self.completed_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.active_tab, text="Active Goals")
        self.notebook.add(self.completed_tab, text="Completed Goals")
        self.notebook.pack(expand=True, fill="both")

        # ---------------------------- Active Goals Tab ----------------------------
        # Add Goal Section
        add_frame = ttk.Frame(self.active_tab, padding=20)
        add_frame.pack(fill="x")
        
        ttk.Label(add_frame, text="Add New Goal", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=5, pady=10)
        
        # Input fields
        ttk.Label(add_frame, text="Goal Name").grid(row=1, column=0)
        self.goal_name = ttk.Entry(add_frame, width=20)
        self.goal_name.grid(row=2, column=0, padx=5)

        ttk.Label(add_frame, text="Total Target").grid(row=1, column=1)
        self.total_target = ttk.Entry(add_frame, width=10)
        self.total_target.grid(row=2, column=1, padx=5)

        ttk.Label(add_frame, text="Weekly Target").grid(row=1, column=2)
        self.weekly_target = ttk.Entry(add_frame, width=10)
        self.weekly_target.grid(row=2, column=2, padx=5)

        ttk.Label(add_frame, text="Unit").grid(row=1, column=3)
        self.unit = ttk.Entry(add_frame, width=10)
        self.unit.grid(row=2, column=3, padx=5)

        ttk.Button(add_frame, text="Add Goal", command=self.add_goal).grid(row=2, column=4, padx=10)

        # Active Goals Display
        self.active_goals_frame = ttk.Frame(self.active_tab)
        self.active_goals_frame.pack(fill="both", expand=True)
        self.refresh_active_goals()

        # Progress Logging Section
        log_frame = ttk.Frame(self.active_tab)
        log_frame.pack(fill="x", pady=10)
        
        ttk.Label(log_frame, text="Log Daily Progress:").pack(side="left", padx=10)
        self.selected_goal = tk.StringVar()
        self.goal_dropdown = ttk.Combobox(log_frame, textvariable=self.selected_goal, width=25)
        self.goal_dropdown.pack(side="left", padx=5)
        
        ttk.Label(log_frame, text="Progress:").pack(side="left", padx=5)
        self.progress_entry = ttk.Entry(log_frame, width=10)
        self.progress_entry.pack(side="left", padx=5)
        
        ttk.Button(log_frame, text="Log", command=self.log_progress).pack(side="left", padx=5)

        # ---------------------------- Completed Goals Tab ----------------------------
        completed_frame = ttk.Frame(self.completed_tab, padding=20)
        completed_frame.pack(fill="both", expand=True)
        
        ttk.Label(completed_frame, text="Completed Goals", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.completed_dropdown = ttk.Combobox(completed_frame, width=40, state="readonly")
        self.completed_dropdown.pack(pady=10)
        
        ttk.Button(completed_frame, text="View Details", command=self.show_completed_details).pack()

    def refresh_active_goals(self):
        # Clear existing entries
        for widget in self.active_goals_frame.winfo_children():
            widget.destroy()
        
        # Create headers
        headers = ["Goal", "Weekly Target", "Current", "Remaining", "Unit", "Status", ""]
        for col, header in enumerate(headers):
            ttk.Label(self.active_goals_frame, text=header, font=("Arial", 10, "bold")).grid(
                row=0, column=col, padx=10, pady=5, sticky="w"
            )

        # Add goal rows
        for row, goal in enumerate(self.tracker.data["active_goals"], start=1):
            weekly_progress = self.tracker.get_weekly_progress(goal["name"])
            remaining = max(goal["weekly_target"] - weekly_progress, 0)
            status = "✅ On Track" if weekly_progress >= goal["weekly_target"] else "⚠️ Behind"

            ttk.Label(self.active_goals_frame, text=goal["name"]).grid(row=row, column=0, padx=10, sticky="w")
            ttk.Label(self.active_goals_frame, text=f"{goal['weekly_target']}").grid(row=row, column=1, padx=10)
            ttk.Label(self.active_goals_frame, text=f"{weekly_progress:.1f}").grid(row=row, column=2, padx=10)
            ttk.Label(self.active_goals_frame, text=f"{remaining:.1f}").grid(row=row, column=3, padx=10)
            ttk.Label(self.active_goals_frame, text=goal["unit"]).grid(row=row, column=4, padx=10)
            ttk.Label(self.active_goals_frame, text=status).grid(row=row, column=5, padx=10)
            
            # Delete button
            ttk.Button(
                self.active_goals_frame,
                text="❌",
                command=lambda g=goal["name"]: self.delete_goal(g)
            ).grid(row=row, column=6, padx=10)

    def add_goal(self):
        name = self.goal_name.get().strip()
        total = self.total_target.get().strip()
        weekly = self.weekly_target.get().strip()
        unit = self.unit.get().strip()

        if not all([name, total, weekly, unit]):
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            self.tracker.add_goal(name, float(total), float(weekly), unit)
            self.refresh_active_goals()
            self.update_goal_dropdown()
            # Clear input fields
            self.goal_name.delete(0, tk.END)
            self.total_target.delete(0, tk.END)
            self.weekly_target.delete(0, tk.END)
            self.unit.delete(0, tk.END)
            messagebox.showinfo("Success", "Goal added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Invalid number format in targets!")

    def log_progress(self):
        goal_name = self.selected_goal.get()
        progress = self.progress_entry.get().strip()

        if not goal_name:
            messagebox.showerror("Error", "Please select a goal!")
            return
        if not progress:
            messagebox.showerror("Error", "Please enter progress!")
            return

        try:
            progress = float(progress)
            if progress < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Progress must be a positive number!")
            return

        if self.tracker.log_progress(goal_name, progress):
            self.refresh_active_goals()
            self.progress_entry.delete(0, tk.END)
            messagebox.showinfo("Success", "Progress logged successfully!")
        else:
            messagebox.showerror("Error", "Failed to log progress!")

    def delete_goal(self, goal_name):
        if messagebox.askyesno("Confirm Delete", f"Delete goal '{goal_name}'?"):
            self.tracker.delete_goal(goal_name)
            self.refresh_active_goals()
            self.update_goal_dropdown()


    def update_goal_dropdown(self):
        self.goal_dropdown["values"] = [g["name"] for g in self.tracker.data["active_goals"]]
        self.completed_dropdown["values"] = [g["name"] for g in self.tracker.data["completed_goals"]]

    def show_completed_details(self):
        goal_name = self.completed_dropdown.get()
        if not goal_name:
            return

        for goal in self.tracker.data["completed_goals"]:
            if goal["name"] == goal_name:
                total = sum(log["progress"] for log in goal["daily_logs"])
                details = (
                    f"Goal: {goal['name']}\n"
                    f"Total {goal['unit']}: {total:.1f}\n"
                    f"Completed on: {goal.get('completion_date', 'N/A')}\n"
                    f"Days Taken: {len(goal['daily_logs'])}"
                )
                messagebox.showinfo("Completed Goal Details", details)
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = GoalTrackerApp(root)
    root.mainloop()