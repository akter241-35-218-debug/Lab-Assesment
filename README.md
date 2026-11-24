# Pharmacy Shelf - Smart Medicine Expiry Management System

Every morning the system tells the pharmacist ONLY the medicines that need a decision today:
Return / Discount / Other action, sorted by priority. No noise for fast-selling stock.

## Team split
| Member | Folder | Work |
|---|---|---|
| Member 1 | `ai_engine/` | Sales velocity, risk detection, action recommender, priority score |
| Member 2 | `backend/` | DB, CRUD + CSV import API, scheduler, digest API, notifications |
| Member 3 | `frontend/` | Daily digest UI, register, company policies, dashboard |

## Contract
`ai_engine.daily_alerts.get_daily_alerts(medicines, today)` -> list of alerts. See `docs/api-contract.md`.

## Run (backend)
```
cd backend
python -m venv venv && venv\Scripts\activate   # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Run from the project ROOT so `ai_engine` can be imported:
`uvicorn backend.app.main:app --reload`  (or set PYTHONPATH to the root)

## Run (frontend)
`frontend/` has only src files. Create the Vite scaffold first:
```
npm create vite@latest frontend-tmp -- --template react
```
then copy `package.json`, `vite.config.js`, `index.html` into `frontend/` and run `npm install && npm run dev`.

## Run AI engine demo (no DB needed)
```
python -m ai_engine.daily_alerts
```
