# My Planner

A local single-user Flask planner with persistent SQLite tasks and daily, weekly, and monthly views. Add a task for a selected date, mark it complete or incomplete, and review completion counts for a period.

## Run locally

Requires Python 3.10 or later:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python planner.py
```

Open http://127.0.0.1:5000. The database is created automatically in `instance/planner.sqlite3`. Tasks persist across application restarts. The default date uses the host computer's local date; task dates have no time-of-day or timezone semantics.

An optional `SECRET_KEY` environment variable keeps form sessions stable across restarts. Otherwise a random key is generated at startup and old forms must be reloaded after restarting. No credentials are stored in source.

## Behavior

- Dates are validated in YYYY-MM-DD format, from 1900 through 2100.
- Day view shows one date; week view runs Monday through Sunday; month view includes all dates in the selected month.
- December and leap-year month lengths are handled with the calendar library.
- Titles are trimmed, limited to 200 characters, and escaped when displayed.
- Tasks are stored using parameterized SQL, with POST-only changes and session-bound form tokens.
- Completion changes set an explicit state rather than toggling blindly.
- Counts describe tasks in the selected period, not productivity scores.

The create_app factory accepts a `DATABASE` path for isolated test/demo instances. Tests create temporary databases and do not touch personal tasks.

## Verify

```bash
python -m unittest discover -s tests -v
```

Tests cover month/year boundaries, leap years, date validation, persistent task creation, completion changes, missing tasks, form-token validation, and escaped text.

## Scope

This is a local portfolio application, not a hosted multi-user service. There are no accounts, shared access controls, recurrence, reminders, or cloud sync. Do not expose the development server publicly. Existing tasks are not migrated from external tools. This demonstrates a working Flask/SQLite workflow, not statistical modeling or ML.
