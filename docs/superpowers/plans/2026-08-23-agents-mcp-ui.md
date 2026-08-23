# Agents MCP UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dev-only Navbar «وكلاء», صفحة `/wukala`, إدارة مفاتيح `/al-idayat/wukala`, وAPI `agent_tokens` خلف `DEV_MODE`.

**Architecture:** طبقة S3/DB منفصلة للمفاتيح؛ الواجهة تستدعي REST عبر `apiFetch`؛ `DevModeGate` server layout يعيد التوجيه لـ `/` عند تعطيل `NEXT_PUBLIC_DEV_MODE`.

**Tech Stack:** Next.js 15, Tailwind 4, Clerk, FastAPI, SQLAlchemy, Alembic, PostgreSQL.

## Global Constraints

- `NEXT_PUBLIC_DEV_MODE=true` (frontend) و`DEV_MODE=true` (backend) — وإلا redirect `/` أو API 404.
- مسارات: `/wukala` (عامة في dev)، `/al-idayat/wukala` (محمية Clerk).
- بادئة المفتاح: `alb_` + base64url(32 bytes); تخزين SHA-256 فقط.
- حد 5 مفاتيح نشطة لكل مستخدم.
- لا `submit` من MCP — خارج النطاق.

---

### Task 1: Backend — model, migration, service

**Files:** `backend/app/models/agent_token.py`, `007_add_agent_tokens_table.py`, `services/agent_token_service.py`, `schemas/agent_token.py`

**Interfaces — Produces:**
- `ALLOWED_AGENT_SCOPES: frozenset[str]`
- `DEFAULT_AGENT_SCOPES: list[str]`
- `create_agent_token(db, user_id, label, scopes) -> tuple[AgentToken, str]`
- `list_agent_tokens(db, user_id) -> list[AgentToken]`
- `update_agent_token_label(db, user_id, token_id, label) -> AgentToken`
- `delete_agent_token(db, user_id, token_id) -> None`

---

### Task 2: Backend — router + tests

**Files:** `routers/agent_tokens.py`, `main.py`, `tests/test_agent_tokens.py`

**Endpoints:** GET/POST `/api/v1/users/me/agent-tokens`, PATCH/DELETE `.../{id}`

---

### Task 3: Frontend — dev gate, navbar, CSS

**Files:** `dev-mode-gate.tsx`, `agents-nav-link.tsx`, `main-nav.tsx`, `globals.css`

---

### Task 4: Frontend — `/wukala` page

**Files:** `app/wukala/layout.tsx`, `app/wukala/page.tsx`, `components/wukala/wukala-cta-button.tsx`

---

### Task 5: Frontend — keys API + panel + pages

**Files:** `lib/api/agent-tokens.ts`, `lib/agent-token-config.ts`, `agent-tokens-panel.tsx`, `app/al-idayat/wukala/*`, `app/al-idayat/page.tsx`

---

### Task 6: Verify

- `npm run lint` + `npm run build`
- `python -m unittest tests/test_agent_tokens.py`
