# MDO Session Log — 9 Sep 2026

Handoff note for continuing work tomorrow.

## Stack

| Layer | Tech |
|--------|------|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Python FastAPI |
| Database | MariaDB (local service) |
| Node.js | Frontend tooling only |

## How to run

```bash
# Backend (current port)
npm run dev:backend
# -> http://localhost:8001

# Frontend
npm run dev:frontend
# -> usually http://localhost:5173 (may shift to 5174 if busy)
```

Vite proxies:
- `/api/*` → `http://localhost:8001`
- `/uploads/*` → `http://localhost:8001`

DB credentials are in `backend/.env` (`root` user). MariaDB `root` was switched to `mysql_native_password`.

## Masters completed today

All support create / search / edit / delete unless noted.

| Master | Route | Key fields |
|--------|--------|------------|
| Currency | `/currencies` | Currency Name, Status (`currency_id` AUTO_INCREMENT, hidden in UI) |
| Country | `/countries` | Country Name, Country Code, Currency, Status |
| State | `/states` | State, Country, CGST %, SGST %, IGST %, Status |
| Region | `/regions` | Region, State, Status |
| Route | `/routes` | Route Code, Region, Status |
| Place | `/places` | Place, Region, Status |
| Section | `/sections` | Section, Status |
| Company | `/companies` | Name, Company Code, Address, Address2, Place, Region, State, Country, Pin, Phone, Mobile, Email, WhatsApp No, GST No, IE Code, ISO Number, Status, Logo upload |

Left panel order:
Currency → Country → State → Region → Route → Place → Section → Company

## Database tables

Created in MariaDB database `mdo`:

- `currencies`
- `countries`
- `states`
- `regions`
- `routes`
- `places`
- `sections`
- `companies`

Schema source of truth:
- `database/init.sql`
- startup `ensure_schema()` in `backend/app/main.py`

## Important technical notes

1. **Currency Id** is DB auto-number only; not entered in the form and not shown in the list.
2. Company logo files are stored under `backend/uploads/logos/` and served at `/uploads/logos/...`
3. Company location fields use cascading dropdowns: Country → State → Region → Place.
4. Backend was moved to **port 8001** because port 8000 had stuck uvicorn processes earlier.
5. Python DB driver is `mariadb` (not `mysql-connector-python`) to avoid auth plugin issues.
6. `backend/.env` is loaded with an absolute path and `override=True`.

## Key folders

```
MDO/
├── frontend/src/pages/     # Master screens
├── frontend/src/api/       # Frontend API clients
├── frontend/src/components/Sidebar.jsx
├── backend/app/routers/    # FastAPI routers
├── backend/app/schemas.py
├── backend/app/main.py
├── backend/uploads/logos/  # Company logos
├── database/init.sql
└── package.json            # npm run scripts
```

## Suggested next steps (tomorrow)

1. Start backend + frontend and verify each master page loads.
2. Confirm Company logo upload/display still works.
3. Decide next master/module to build.
4. Optional cleanup: free/kill any leftover process on port 8000; keep using 8001 or standardize back to 8000.
5. Optional: git commit today’s work if version control is needed.

## Status at end of day

Environment + all listed masters are implemented and wired into the left panel. Backend was last confirmed healthy on `http://localhost:8001`.
