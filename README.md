# Hospital Management App - Starter

This is a starter Flask application built for the course constraints:
- Flask backend
- Jinja2 templates + HTML/CSS + Bootstrap (CDN) for frontend
- SQLite (programmatic creation via SQLAlchemy `db.create_all()`)
- Manual server-side validation
- JSON API endpoints (flask routes returning JSON)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
# open http://127.0.0.1:5000/
```

Default seeded admin account:
- username: admin
- email: admin@example.com
- password: adminpass
