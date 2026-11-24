# Backend (Member 2) - FastAPI + MySQL

Run everything **from the project root** (`pharmacy-shelf/`).

```bash
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env                   # then set DATABASE_URL
mysql -u root -p -e "CREATE DATABASE pharmacy_shelf CHARACTER SET utf8mb4"

python -m backend.scripts.seed_demo                    # optional: load data/sample_*.csv
uvicorn backend.app.main:app --reload                  # http://localhost:8000/docs
pytest                                                 # backend + ai_engine tests
```
No MySQL yet? Use `DATABASE_URL=sqlite:///./pharmacy_shelf.db` for development.

Demo digest for the sample dates: `GET /alerts/today?today=2026-11-24`
(regenerate CSVs for another date: `python backend/scripts/make_sample_data.py --today YYYY-MM-DD`).

Notifications (Email/Telegram/SMS) are off by default; enable in `backend/.env`.
The scheduler runs the digest daily at `DIGEST_HOUR:DIGEST_MINUTE` (Asia/Dhaka) while the server is running.
