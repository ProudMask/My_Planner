"""A local single-user task planner with SQLite persistence."""
import calendar
from datetime import date, timedelta
import hmac
import os
from pathlib import Path
import secrets
import sqlite3
from flask import Flask, abort, g, redirect, render_template, request, session, url_for


def parse_date(value):
    try:
        result = date.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValueError('Enter a valid date in YYYY-MM-DD format') from exc
    if result.isoformat() != value or not 1900 <= result.year <= 2100:
        raise ValueError('Choose a date between 1900-01-01 and 2100-12-31')
    return result


def period_bounds(selected, view):
    if view == 'day':
        return selected, selected
    if view == 'week':
        start = selected - timedelta(days=selected.weekday())
        return start, start + timedelta(days=6)
    if view == 'month':
        return selected.replace(day=1), selected.replace(day=calendar.monthrange(selected.year, selected.month)[1])
    raise ValueError('View must be day, week, or month')


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32), DATABASE=str(Path(app.instance_path) / 'planner.sqlite3'), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=16384)
    if config:
        app.config.update(config)
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)

    def connection():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row
            g.db.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, due_date TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)))')
            g.db.commit()
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    @app.before_request
    def protect_forms():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        if request.method == 'POST':
            token = request.form.get('csrf_token', '')
            if not hmac.compare_digest(token.encode('utf-8'), session['csrf_token'].encode('utf-8')):
                abort(400, 'Invalid form token. Reload the planner and try again.')

    def selection(values):
        try:
            selected = parse_date(values.get('date', date.today().isoformat()))
            view = values.get('view', 'day')
            period_bounds(selected, view)
            return selected, view
        except ValueError as exc:
            abort(400, str(exc))

    @app.get('/')
    def index():
        selected, view = selection(request.args)
        start, end = period_bounds(selected, view)
        tasks = connection().execute('SELECT * FROM tasks WHERE due_date BETWEEN ? AND ? ORDER BY due_date, completed, id', (start.isoformat(), end.isoformat())).fetchall()
        completed = sum(task['completed'] for task in tasks)
        days = [selected.replace(day=d) for d in range(1, calendar.monthrange(selected.year, selected.month)[1] + 1)]
        return render_template('index.html', selected=selected, view=view, start=start, end=end, tasks=tasks, completed=completed, days=days)

    @app.post('/tasks')
    def add_task():
        selected, view = selection(request.form)
        title = request.form.get('title', '').strip()
        if not 1 <= len(title) <= 200:
            abort(400, 'Task title must contain 1 to 200 characters')
        db = connection()
        db.execute('INSERT INTO tasks(title, due_date) VALUES (?, ?)', (title, selected.isoformat()))
        db.commit()
        return redirect(url_for('index', date=selected.isoformat(), view=view), code=303)

    @app.post('/tasks/<int:task_id>/complete')
    def complete_task(task_id):
        selected, view = selection(request.form)
        completed = request.form.get('completed')
        if completed not in {'0', '1'}:
            abort(400, 'Completed must be 0 or 1')
        db = connection()
        result = db.execute('UPDATE tasks SET completed=? WHERE id=?', (int(completed), task_id))
        if not result.rowcount:
            abort(404, 'Task not found')
        db.commit()
        return redirect(url_for('index', date=selected.isoformat(), view=view), code=303)

    return app


app = create_app()

if __name__ == '__main__':
    app.run()
