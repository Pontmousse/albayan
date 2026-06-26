#!/usr/bin/env bash

# launch.sh — Run from project root.
# Uses conda env (see CondaEnv below). Starts DB (Docker), Alembic migrations, backend, and frontend.

CondaEnv="${CONDA_ENV_NAME:-my_env1}"
ProjectRoot="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
backendPath="$ProjectRoot/backend"
frontendPath="$ProjectRoot/frontend"
dbPath="$ProjectRoot/backend/database"

sep="================================================================================"
sepShort="--------------------------------------------------------------------------------"

open_terminal() {
    local title="$1"
    local cmd="$2"

    if command -v gnome-terminal >/dev/null 2>&1; then
        gnome-terminal --title="$title" -- bash -lc "$cmd; exec bash"
    elif command -v konsole >/dev/null 2>&1; then
        konsole --new-tab -p tabtitle="$title" -e bash -lc "$cmd; exec bash" &
    elif command -v xfce4-terminal >/dev/null 2>&1; then
        xfce4-terminal --title="$title" -e bash -lc "$cmd; exec bash" &
    elif command -v xterm >/dev/null 2>&1; then
        xterm -T "$title" -e bash -lc "$cmd; exec bash" &
    else
        echo "  No graphical terminal found. Run manually in a separate shell:"
        echo "    $cmd"
    fi
}

wait_for_postgres() {
    local retries="${1:-20}"
    while [ "$retries" -gt 0 ]; do
        if docker exec albayan_postgres pg_isready -U albayan_user -d albayan >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        retries=$((retries - 1))
    done
    return 1
}

conda_activate_prefix='eval "$(conda shell.bash hook)" && conda activate "'"$CondaEnv"'"'

echo ""
echo "$sep"
echo "  LAUNCH SCRIPT - Al-Bayan Dev Environment (conda: $CondaEnv)"
echo "$sep"
echo ""

# [1/4] Database (Docker PostgreSQL)
echo "$sepShort"
echo "  [1/4] STARTING: PostgreSQL (Docker)"
echo "$sepShort"

postgresPort="5434"
if [ -f "$dbPath/.env" ]; then
    # shellcheck disable=SC1090
    set -a && source "$dbPath/.env" && set +a
    postgresPort="${POSTGRES_PORT:-5434}"
fi

if command -v docker >/dev/null 2>&1; then
    (
        cd "$dbPath" || exit 1
        docker compose down -v --remove-orphans 2>/dev/null || true
        docker compose up -d
    )
    exitCode=$?

    if [ "$exitCode" -eq 0 ]; then
        echo "  PostgreSQL started (container: albayan_postgres)."
        echo "  Ephemeral tmpfs — data is erased when the container stops or restarts."
        echo "  Port ${postgresPort} (host) -> 5432 (container)."
        echo "  Waiting for Postgres to accept connections..."
        if wait_for_postgres 20; then
            echo "  Postgres is ready."
        else
            echo "  Warning: Postgres health check timed out. Migrations may fail."
        fi
    else
        echo "  Docker compose returned exit code $exitCode. Check Docker and port ${postgresPort}."
    fi
else
    echo "  Docker not found. Start PostgreSQL manually or install Docker."
fi

echo ""

# [2/4] Alembic migrations (conda)
echo "$sepShort"
echo "  [2/4] RUNNING: Alembic migrations (conda: $CondaEnv)"
echo "$sepShort"

if command -v conda >/dev/null 2>&1; then
    if bash -lc "$conda_activate_prefix && cd \"$backendPath\" && alembic upgrade head"; then
        echo "  Migrations applied (alembic upgrade head)."
    else
        echo "  Migration failed. Ensure conda env \"$CondaEnv\" exists and requirements are installed:"
        echo "    conda activate $CondaEnv && pip install -r backend/requirements.txt"
    fi
else
    echo "  conda not found. Run migrations manually:"
    echo "    cd backend && alembic upgrade head"
fi

echo ""

# [3/4] Backend (conda + uvicorn)
echo "$sepShort"
echo "  [3/4] OPENING: Backend (FastAPI / uvicorn) in conda env $CondaEnv"
echo "$sepShort"

backendCmd="$conda_activate_prefix && cd \"$backendPath\" && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
open_terminal "Backend - Al-Bayan" "$backendCmd"

echo ""

# [4/4] Frontend (Next.js dev)
echo "$sepShort"
echo "  [4/4] OPENING: Frontend (Next.js dev)"
echo "$sepShort"

frontendCmd="cd \"$frontendPath\" && npm run dev"
open_terminal "Frontend - Al-Bayan" "$frontendCmd"

# LAN IP for mobile testing
lanIp=""
allIps="$(ip -4 addr show scope global 2>/dev/null | awk '/inet / {print $2}' | cut -d/ -f1 | grep -v '^169\.' || true)"
preferred="$(echo "$allIps" | grep '^192\.168\.' | head -n 1 || true)"
if [ -n "$preferred" ]; then
    lanIp="$preferred"
else
    fallback="$(echo "$allIps" | grep '^10\.' | head -n 1 || true)"
    if [ -n "$fallback" ]; then
        lanIp="$fallback"
    else
        lanIp="$(echo "$allIps" | grep -vE '^172\.(1[6-9]|2[0-9]|3[0-1])\.' | head -n 1 || true)"
    fi
fi
if [ -z "$lanIp" ]; then
    lanIp="???"
fi

echo ""
echo -e "\033[36m  Auth (Clerk headless):\033[0m"
echo "    Register:  http://localhost:3000/tasjil"
echo "    Sign in:   http://localhost:3000/tawajjuh"
echo "    Settings:  http://localhost:3000/al-idayat  (requires session)"
echo ""
echo -e "\033[33m  Before first run, configure:\033[0m"
echo "    - frontend/.env.local  (NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY, ...)"
echo "    - backend/.env         (DATABASE_URL, CLERK_SECRET_KEY)"
echo "    See frontend/.env.example and backend/.env.example"
echo ""

echo ""
echo "  Done. DB (Docker), Migrations, Backend, and Frontend."
echo "  DB: localhost:${postgresPort}   Backend: http://localhost:8000   Frontend: http://localhost:3000"
echo "  LAN Frontend: http://${lanIp}:3000  (for mobile testing; configure Clerk allowed origins if needed)"
echo ""
