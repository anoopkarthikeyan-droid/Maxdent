# Maxdent

MDO (MaxDenta Lab / Master Data Office) — React + Vite frontend, Tailwind CSS, Python FastAPI backend, MariaDB database.

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

## Run with Docker (full app)

```bash
docker compose --profile app up -d --build
```

Open http://localhost:8080 (on the VPS: `http://YOUR_VPS_IP:8080`).

```bash
docker compose --profile app ps
docker compose --profile app logs -f
docker compose --profile app down
```

MariaDB only (local development):

```bash
docker compose up -d mariadb
```

## Run services without Docker

```bash
# Ensure schema (once)
npm run db:init

# Frontend — http://localhost:5173
npm run dev:frontend

# Backend — http://localhost:8001
npm run dev:backend
```

Open http://localhost:5173. Last built screen: Case Study (`/case-studies`).

API health: `GET http://localhost:8001/health`  
Vite proxies `/api` and `/uploads` to FastAPI on port 8001.
