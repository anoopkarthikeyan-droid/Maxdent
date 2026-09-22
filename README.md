# MDO Full-Stack Environment

React + Vite frontend, Tailwind CSS, Python FastAPI backend, MariaDB database.

Node.js is used only for the frontend toolchain (Vite / npm).

## Structure

```
MDO/
├── frontend/          # React (Vite) + Tailwind CSS
├── backend/           # FastAPI (Python) API
├── database/          # MariaDB init SQL
├── scripts/           # DB helpers
└── docker-compose.yml # Optional MariaDB via Docker
```

## Features

- **Currency Master** — create / search / edit / delete currencies (`currency_id`, `currency_name`, `status`)

## Run services

```bash
# Ensure schema (once)
npm run db:init

# Frontend — http://localhost:5173
npm run dev:frontend

# Backend — http://localhost:8000
npm run dev:backend
```

Open http://localhost:5173 for Currency Master.

API: `GET/POST /currencies`, `PUT/DELETE /currencies/{id}`  
Vite proxies `/api/*` → FastAPI on port 8000.
