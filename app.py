from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import logging

app = Flask(__name__)

logging.basicConfig(
    filename='todo_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def init_db():
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignee TEXT,
                date TEXT,
                task TEXT,
                status TEXT
            )
        """)

        conn.commit()
        conn.close()
        logging.info('Database initialized')

    except Exception as e:
        logging.error(f'DB Init Error: {e}')


@app.route('/')
def index():
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM tasks')
        tasks = cursor.fetchall()

        conn.close()

        return render_template('index.html', tasks=tasks)

    except Exception as e:
        logging.error(f'Error fetching tasks: {e}')
        return 'Error loading tasks'


@app.route('/add', methods=['POST'])
def add_task():
    try:
        assignee = request.form['assignee']
        task = request.form['task']
        status = request.form['status']
        date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tasks (assignee, date, task, status)
            VALUES (?, ?, ?, ?)
        """, (assignee, date, task, status))

        conn.commit()
        conn.close()

        logging.info(f'Task added for {assignee}')

    except Exception as e:
        logging.error(f'Error adding task: {e}')

    return redirect('/')


@app.route('/update/<int:id>', methods=['POST'])
def update_task(id):
    try:
        new_status = request.form['status']

        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tasks SET status=? WHERE id=?
        """, (new_status, id))

        conn.commit()
        conn.close()

        logging.info(f'Task {id} updated')

    except Exception as e:
        logging.error(f'Error updating task: {e}')

    return redirect('/')


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)