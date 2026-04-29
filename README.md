# OrderStricker

Catalog browsing with a chat rail that narrows which products appear on the wall. The backend asks **Ollama** to interpret shopper messages as product-name lists matching the seeded catalog (**50 items**). Without Ollama, the site still loads and the assistant runs in **degraded** mode (wall unchanged until Ollama is available).

Optional **MongoDB** and **Redis** add persistence and caching; with neither, everything runs **in-memory** (fine for local development and tests).

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python** | 3.10 or newer (`python --version`). |
| **Node.js** | 18+ recommended (for the Vite + React frontend). |
| **Ollama** | Optional but needed for AI-driven chat refinements. Default URL: `http://127.0.0.1:11434`, default model: `llama3.2`. |
| **Docker** | Optional. Used only if you want local MongoDB/Redis via Compose. |
| **Windows** | See [Windows environment](#windows-environment) for venv activation, env vars, and paths. |

---

## Windows environment

These notes match **Windows 10/11** with **PowerShell** (recommended) or **Command Prompt**. Install **Python 3.10+** and **Node.js** from the official installers (check “Add Python to PATH” during setup). For Docker-based Mongo/Redis, use **Docker Desktop** (WSL2 backend is recommended for Linux containers).

### Python virtual environment

From the project root (replace **`py`** with **`python`** if that is what your install provides):

**PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

If script execution is disabled, run once (current user):  
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`  
—or activate with **Command Prompt** instead.

**Command Prompt (`cmd.exe`):**

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -e .
```

Leave the venv with **`deactivate`**.

### Run the API and frontend

After activation, start the API and, in another terminal, the frontend—same commands as in [§2](#2-python-backend-api) and [§3](#3-frontend-web-ui): **`orderstricker-api`** (or **`python -m orderstricker.api.main`**), then **`cd frontend`**, **`npm install`**, **`npm run dev`**.

### Environment variables (Windows)

Values apply only to that terminal session unless you set them in *System → Environment Variables* or a profile script.

**PowerShell:**

```powershell
$env:PORT = "8000"
$env:RELOAD = "1"
$env:MONGO_URI = "mongodb://127.0.0.1:27017"
$env:REDIS_URL = "redis://127.0.0.1:6379"
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "llama3.2"
$env:CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
```

**Command Prompt:**

```bat
set PORT=8000
set RELOAD=1
set MONGO_URI=mongodb://127.0.0.1:27017
set REDIS_URL=redis://127.0.0.1:6379
set OLLAMA_HOST=http://127.0.0.1:11434
set OLLAMA_MODEL=llama3.2
set CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Docker Compose

Start **Docker Desktop**, then:

```powershell
docker compose up -d
```

### Offline wheels folder (paths)

PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path vendor\pip-wheels | Out-Null
pip wheel -w vendor\pip-wheels ".[dev]"
pip install --no-index --find-links vendor\pip-wheels -e .
```

Command Prompt:

```bat
mkdir vendor\pip-wheels 2>nul
pip wheel -w vendor\pip-wheels ".[dev]"
pip install --no-index --find-links vendor\pip-wheels -e .
```

### Ollama on Windows

Install from [ollama.com](https://ollama.com/) and keep the app/service running so **`http://127.0.0.1:11434`** responds. **`ollama pull llama3.2`** runs in PowerShell or cmd like any other CLI.

---

## 1. Clone and enter the project

```bash
git clone <repository-url>
cd OrderStricker
```

---

## 2. Python backend (API)

Create a virtual environment, install the package in editable mode, and run the server.

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux; on Windows see [Windows environment](#windows-environment)
pip install --upgrade pip
pip install -e .
```

(Optional dev dependencies, including pytest: `pip install -e ".[dev]"`.)

**Start the API** ( listens on **`0.0.0.0:8000`** unless you override `PORT`):

```bash
orderstricker-api
```

Equivalent:

```bash
python -m orderstricker.api.main
```

Useful environment variables:

- **`PORT`** — HTTP port (default `8000`).
- **`RELOAD`** — Set to `1` or `true` for auto-reload during development.

---

## 3. Frontend (web UI)

In a **second terminal** (with the API still running):

```bash
cd frontend
npm install
npm run dev
```

Vite serves the app at **[http://127.0.0.1:5173](http://127.0.0.1:5173)** and **proxies `/api`** to **`http://127.0.0.1:8000`**.

If your API runs on another host/port, adjust `frontend/vite.config.ts` (`server.proxy["/api"].target`) or run the frontend with a matching proxy.

---

## 4. Ollama (chat refinements)

1. Install [Ollama](https://ollama.com/) and ensure it is running (default listens on port **11434**).
2. Pull the model name you plan to use, for example (must match **`OLLAMA_MODEL`** if you change it):

   ```bash
   ollama pull llama3.2
   ```

3. Optional environment variables:

   - **`OLLAMA_HOST`** — Base URL for the Ollama API (default `http://127.0.0.1:11434`).
   - **`OLLAMA_MODEL`** — Model tag (default `llama3.2`).

If Ollama is stopped or unreachable, chat still succeeds with a friendly message and the product wall does not reset unexpectedly.

---

## 5. Optional persistence (MongoDB + Redis)

Everything works **in-memory** without these. Set them when you want catalog/user state backed by Mongo and optional Redis caching.

| Variable | Meaning |
|----------|---------|
| **`MONGO_URI`** (alias **`ORDERSTRICKER_MONGO_URI`**) | e.g. `mongodb://localhost:27017` — enables Mongo-backed catalog and related session storage. |
| **`ORDERSTRICKER_MONGO_DB`** | Database name (default **`orderstricker`**). |
| **`REDIS_URL`** (alias **`ORDERSTRICKER_REDIS_URL`**) | Enables Redis-backed catalog caching, idempotency (with Mongo), and conversation session overlays when wired. |
| **`ORDERSTRICKER_CATALOG_CACHE_SEC`** | Catalog cache TTL in seconds (default **90**, minimum enforced in code). |
| **`ORDERSTRICKER_CONVERSATION_REDIS_TTL_SEC`** | Conversation Redis TTL (default **86400**, minimum enforced). |

Bring up MongoDB and Redis locally:

```bash
docker compose up -d
```

Then point the API at them, for example (**bash**):

```bash
export MONGO_URI="mongodb://127.0.0.1:27017"
export REDIS_URL="redis://127.0.0.1:6379"
```

On **Windows**, set the same variables in PowerShell or `cmd` as shown in [Environment variables](#environment-variables-windows).

`docker-compose.yml` exposes MongoDB on **27017** and Redis on **6379**.

---

## 6. CORS

The API defaults to allowing origins **`http://localhost:5173`** and **`http://127.0.0.1:5173`**. Override with **`CORS_ORIGINS`** (comma-separated) if your frontend runs elsewhere.

---

## 7. Working offline

The stack is **local-first**: the browser talks to Vite on your machine, Vite proxies to the API on **127.0.0.1**, and (by default) the catalog and chat session state live **in memory**. You do **not** need the public internet to run the app as long as you prepare once while online (or copy a machine that was already set up).

### What works without any network

- **API + UI** — `orderstricker-api` and `npm run dev`; open **http://127.0.0.1:5173**.
- **Catalog browsing** — Full seeded catalog with no external services.
- **Chat (degraded)** — If Ollama is not running, chat returns a friendly message and the product wall does not break.
- **Chat (full)** — **Ollama** runs **entirely on your computer**; after you have pulled a model, inference does not use the internet.

### One-time prep (do this while you still have access to the internet)

1. **Repository** — Clone (or copy) the project so the full tree is on disk.
2. **Python** — Create the venv and run `pip install -e .` (and optionally `pip install -e ".[dev]"`).
3. **Frontend** — In `frontend/`, run `npm install` so **`node_modules/`** exists. After that, `npm run dev` works offline unless you change `package.json` or remove `node_modules`.
4. **Ollama (recommended)** — Install Ollama, start it, then pull the model you will use:

   ```bash
   ollama pull llama3.2
   ```

   Use the same name as **`OLLAMA_MODEL`** (default `llama3.2`). After the pull completes, chat refinements work offline whenever Ollama is running locally.
5. **Optional: Docker DBs** — If you rely on Compose for MongoDB/Redis, run `docker compose pull` once before going offline so images exist locally (`docker compose up -d` then works offline).
6. **Optional: Offline-friendly Python reinstalls** — If you might need to rebuild the venv without network access, prefetch dependency wheels once (online), from the project root:

   ```bash
   mkdir -p vendor/pip-wheels
   pip wheel -w vendor/pip-wheels ".[dev]"
   ```

   Later, offline (with the same repo checkout), create a fresh venv and install without hitting PyPI:

   ```bash
   pip install --no-index --find-links vendor/pip-wheels -e .
   ```

   Omit `".[dev]"` in the wheel step if you only need runtime dependencies. You can add **`vendor/`** to `.gitignore` so wheel files are not committed. On **Windows**, use the paths and commands in [Offline wheels folder](#offline-wheels-folder-paths).

### Typical offline day

**macOS / Linux:**

```bash
# Terminal 1 — API
source .venv/bin/activate
orderstricker-api

# Terminal 2 — ensure Ollama is running locally if you want AI chat (often: system tray / `ollama serve`)
# Terminal 3 — frontend
cd frontend && npm run dev
```

**Windows** — Activate the venv in each terminal that runs Python commands (see [Windows environment](#windows-environment)); then **`orderstricker-api`**, **`cd frontend`**, **`npm run dev`**.

Use **localhost / 127.0.0.1** URLs only; no VPN or SaaS dependency is required for this app.

---

## Quick checklist

1. Activate venv → `pip install -e .` → `orderstricker-api`. On **Windows**, use `.\.venv\Scripts\Activate.ps1` or `.venv\Scripts\activate.bat` (see [above](#windows-environment)).
2. `cd frontend && npm install && npm run dev`.
3. Open **http://127.0.0.1:5173**.
4. (Recommended) Run Ollama and `ollama pull` your chosen model so chat narrows the product wall.
5. **Offline:** complete the [one-time prep](#7-working-offline) while online; then run the same commands without internet.
