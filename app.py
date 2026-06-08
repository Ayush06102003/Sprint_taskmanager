from flask import Flask, render_template, request, redirect,send_file
from openpyxl import Workbook
import psycopg2
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)

# ---------------- LOGGING ----------------

logging.basicConfig(
    filename='todo_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------------- DB CONNECTION ----------------

def get_connection():
    return psycopg2.connect(
        os.getenv("DATABASE_URL")
    )

# ---------------- DB INIT ----------------

def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
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
        cursor.close()
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

        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if assignee_filter:
            query += " AND assignee=%s"
            params.append(assignee_filter)

        if status_filter:
            query += " AND status=%s"
            params.append(status_filter)

        if sprint_filter:
            query += " AND sprint=%s"
            params.append(sprint_filter)

        query += " ORDER BY id DESC"

        cursor.execute(query, params)
        tasks = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'index.html',
            tasks=tasks
        )

    except Exception as e:
        logging.error(f"Error fetching tasks: {e}")
        return f"Error loading tasks: {e}"

# ----------------Export to excel--------

@app.route('/export_excel')
def export_excel():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               sprint,
               assignee,
               epic,
               task,
               status,
               effort,
               hours_spent,
               remaining,
               comment,
               date
        FROM tasks
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    wb = Workbook()
    ws = wb.active

    ws.title = "Sprint Tasks"

    ws.append([
        "Id"
        "Sprint",
        "Assignee",
        "Epic",
        "Task",
        "Status",
        "Effort",
        "Hours Spent",
        "Remaining",
        "Comment",
        "Date"
    ])

    for row in rows:
        ws.append(row)

    filename = "Sprint_Tasks.xlsx"

    wb.save(filename)

    cursor.close()
    conn.close()

    return send_file(
        filename,
        as_attachment=True
    )

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

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tasks
            (
                assignee,
                date,
                sprint,
                epic,
                task,
                status,
                effort,
                hours_spent,
                remaining,
                comment
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            assignee,
            datetime.now(
                ZoneInfo("Asia/Kolkata")
            ).strftime("%Y-%m-%d"),
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

        cursor.close()
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

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT effort FROM tasks WHERE id=%s",
            (id,)
        )

        result = cursor.fetchone()

        if not result:
            return "Task not found"

        effort = result[0]

        remaining = effort - hours_spent

        if status == "Completed" and remaining > 0:
            return "❌ Remaining must be 0 to complete"

        cursor.execute("""
            UPDATE tasks
            SET status=%s,
                hours_spent=%s,
                remaining=%s,
                comment=%s
            WHERE id=%s
        """, (
            status,
            hours_spent,
            remaining,
            comment,
            id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        logging.info(f"Task {id} updated")

    except Exception as e:
        logging.error(f"Error updating task: {e}")

    return redirect('/')

# ---------------- DELETE ----------------

@app.route('/delete/<int:id>', methods=['POST'])
def delete_task(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM tasks WHERE id=%s",
            (id,)
        )

        conn.commit()

        cursor.close()
        conn.close()

        logging.info(f"Task {id} deleted")

    except Exception as e:
        logging.error(f"Error deleting task: {e}")

    return redirect('/')

# ---------------- STARTUP ----------------

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
