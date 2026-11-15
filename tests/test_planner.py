from datetime import date
import tempfile
import unittest
from pathlib import Path
from planner import create_app, parse_date, period_bounds


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = {'TESTING': True, 'SECRET_KEY': 'test-only', 'DATABASE': str(Path(self.temp.name) / 'tasks.sqlite3')}
        self.client = create_app(self.config).test_client()
        self.client.get('/')
        with self.client.session_transaction() as session:
            self.token = session['csrf_token']

    def tearDown(self):
        self.temp.cleanup()

    def add(self, title='Study statistics', day='2026-12-31'):
        return self.client.post('/tasks', data={'title': title, 'date': day, 'csrf_token': self.token})

    def test_december_and_leap_year(self):
        self.assertEqual(period_bounds(date(2026, 12, 15), 'month')[1], date(2026, 12, 31))
        self.assertEqual(period_bounds(date(2028, 2, 15), 'month')[1], date(2028, 2, 29))
        self.assertEqual(period_bounds(date(2027, 1, 1), 'week'), (date(2026, 12, 28), date(2027, 1, 3)))
        self.assertEqual(self.client.get('/?date=2026-12-31&view=month').status_code, 200)

    def test_invalid_date_and_view(self):
        for query in ('date=bad', 'date=2026-02-30', 'date=2101-01-01', 'view=year'):
            self.assertEqual(self.client.get('/?' + query).status_code, 400)

    def test_task_persistence_and_period(self):
        self.assertEqual(self.add().status_code, 303)
        another = create_app(self.config).test_client()
        self.assertIn(b'Study statistics', another.get('/?date=2026-12-31').data)
        self.assertNotIn(b'Study statistics', another.get('/?date=2026-12-30').data)
        self.assertIn(b'Study statistics', another.get('/?date=2027-01-01&view=week').data)

    def test_completion_idempotent(self):
        self.add()
        for _ in range(2):
            response = self.client.post('/tasks/1/complete', data={'completed': '1', 'date': '2026-12-31', 'csrf_token': self.token})
            self.assertEqual(response.status_code, 303)
        self.assertIn(b'1 of 1 tasks completed', self.client.get('/?date=2026-12-31').data)

    def test_tokens_and_invalid_titles(self):
        self.assertEqual(self.client.post('/tasks', data={'title': 'test'}).status_code, 400)
        self.assertEqual(self.client.post('/tasks', data={'title': 'test', 'csrf_token': 'غير صالح'}).status_code, 400)
        for title in (' ', 'x' * 201):
            self.assertEqual(self.add(title).status_code, 400)

    def test_missing_task(self):
        self.assertEqual(self.client.post('/tasks/999/complete', data={'completed': '1', 'csrf_token': self.token}).status_code, 404)

    def test_escape_title(self):
        self.add('<script>alert(1)</script>')
        page = self.client.get('/?date=2026-12-31').data
        self.assertIn(b'&lt;script&gt;', page)
        self.assertNotIn(b'<script>alert', page)


if __name__ == '__main__':
    unittest.main()
