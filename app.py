from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import logging

app = Flask(__name__)

# ---------------- LOGGING ----------------

logging.basicConfig(
    filename='todo_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------------- DB INIT ----------------

def init_db():
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignee TEXT,
                date TEXT,
                sprint TEXT,
                epic TEXT,
                task TEXT,
                status TEXT,
                effort INTEGER,
                hours_spent INTEGER,
                remaining INTEGER,
                comment TEXT
            )
        """)

        conn.commit()
        conn.close()

        logging.info("Database initialized")

    except Exception as e:
        logging.error(f"DB Init Error: {e}")


# ---------------- HOME WITH FILTER ----------------

@app.route('/')
def index():
    try:
        assignee_filter = request.args.get('assignee')
        status_filter = request.args.get('status')
        sprint_filter = request.args.get('sprint')
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if assignee_filter:
            query += " AND assignee=?"
            params.append(assignee_filter)

        if status_filter:
            query += " AND status=?"
            params.append(status_filter)

        if sprint_filter:
            query += " AND sprint=?"
            params.append(sprint_filter)

        cursor.execute(query, params)
        tasks = cursor.fetchall()

        conn.close()

        return render_template('index.html', tasks=tasks)

    except Exception as e:
        logging.error(f"Error fetching tasks: {e}")
        return "Error loading tasks"


# ---------------- ADD ----------------

@app.route('/add', methods=['POST'])
def add_task():
    try:
        data = request.form

        assignee = data['assignee']
        sprint = data['sprint']
        epic = data['epic']
        task = data['task']
        status = data['status']

        effort = int(data['effort'])
        hours_spent = int(data['hours_spent'])

        remaining = effort - hours_spent

        comment = data.get('comment', '')

        if status == "Completed" and remaining > 0:
            return "❌ Cannot mark complete unless remaining = 0"

        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tasks
            (assignee, date, sprint, epic, task, status, effort, hours_spent, remaining, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assignee,
            datetime.now().strftime("%Y-%m-%d"),
            sprint,
            epic,
            task,
            status,
            effort,
            hours_spent,
            remaining,
            comment
        ))

        conn.commit()
        conn.close()

        logging.info(f"Task added for {assignee}")

    except Exception as e:
        logging.error(f"Error adding task: {e}")

    return redirect('/')


# ---------------- UPDATE ----------------

@app.route('/update/<int:id>', methods=['POST'])
def update_task(id):
    try:
        status = request.form['status']
        hours_spent = int(request.form['hours_spent'])
        comment = request.form.get('comment', '')

        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT effort FROM tasks WHERE id=?",
            (id,)
        )

        effort = cursor.fetchone()[0]

        remaining = effort - hours_spent

        if status == "Completed" and remaining > 0:
            return "❌ Remaining must be 0 to complete"

        cursor.execute("""
            UPDATE tasks
            SET status=?,
                hours_spent=?,
                remaining=?,
                comment=?
            WHERE id=?
        """, (
            status,
            hours_spent,
            remaining,
            comment,
            id
        ))

        conn.commit()
        conn.close()

        logging.info(f"Task {id} updated")

    except Exception as e:
        logging.error(f"Error updating task: {e}")

    return redirect('/')


# ---------------- DELETE ----------------

@app.route('/delete/<int:id>', methods=['POST'])
def delete_task(id):
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM tasks WHERE id=?",
            (id,)
        )

        conn.commit()
        conn.close()

        logging.info(f"Task {id} deleted")

    except Exception as e:
        logging.error(f"Error deleting task: {e}")

    return redirect('/')

import os

if os.path.exists("tasks.db"):
    os.remove("tasks.db")
    
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)