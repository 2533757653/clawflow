# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClawFlow is a platform for dynamically building and managing AI Agent organizations. It integrates with OpenClaw (an AI Agent framework where each Agent is defined by Markdown files) to deploy and coordinate multi-agent workflows.

Key distinction: **Roles = OpenClaw Agents**. Each role is a separate OpenClaw Agent with its own workspace (SOUL.md, IDENTITY.md, skills/, memory/).

## Commands

```bash
# Backend (FastAPI serves both API and built frontend)
cd api
uvicorn main:app --reload --port 8000

# Frontend (dev mode, proxy to backend)
cd web
npm install
npm run dev

# Build frontend for production
cd web
npm run build

# Run tests
cd api
pytest
pytest api/tests/test_roles.py   # run specific test file
```

## Architecture

```
clawflow/
├── api/                    # FastAPI backend
│   ├── main.py            # App entry, serves built frontend from web/dist/
│   ├── routers/           # API endpoints (organizations, roles, tasks, dataflows, knowledge, skills, rag, memory, agency, execution)
│   ├── models/            # Pydantic models
│   └── services/         # Business logic (openclaw_adapter, storage, rag_service, etc.)
├── web/                    # React + TypeScript frontend
│   ├── src/pages/         # Page components
│   ├── src/components/    # Reusable UI components
│   ├── src/services/     # API client (api.ts, executionApi.ts, roleSuggestionApi.ts)
│   ├── src/stores/       # Zustand state management
│   └── src/types/        # TypeScript types
├── data/                   # Local JSON storage (organizations, knowledge, skills, roles, memory, rag)
├── agents/                # Deployed OpenClaw Agents (one dir per role)
└── docs/prompts/          # LLM prompt templates for features
```

### Storage Separation

| Content | Storage |
|---------|---------|
| Role definitions, skills, knowledge, dataflows, tasks | `data/` (JSON files) |
| Deployed OpenClaw Agents | `agents/` directory |
| Role = OpenClaw Agent workspace | `agents/{role_name}/` (SOUL.md, IDENTITY.md, skills/, memory/) |

### Frontend-Backend Integration

FastAPI serves the built React app at `/`. When building frontend (`npm run build`), output goes to `web/dist/`, which FastAPI mounts at root. For active development, run `npm run dev` in `web/` and proxy requests to the backend.

### Key API Routes

- `GET/POST /api/v1/organizations` — Organization CRUD
- `POST /api/v1/organizations/{id}/deploy` — Deploy to OpenClaw
- `GET/POST /api/v1/roles` — Global role management (roles stored globally in `data/roles/`, referenced by organizations)
- `GET/POST /api/v1/organizations/{org_id}/tasks` — Task management per organization
- `GET/POST /api/v1/organizations/{org_id}/dataflows` — DataFlow nodes and edges
- `GET/POST /api/v1/organizations/{org_id}/knowledge` — Organization-level knowledge base
- `GET /api/v1/skills/search` — ClawHub skill search
- `POST /api/v1/skills/{id}/install` — Install skill to a role
- `GET /api/v1/rag/query` — RAG knowledge base query
- `GET/POST /api/v1/memory` — Context memory management
- `POST /api/v1/execution/execute` — Execute workflow
- `GET /api/v1/roles/suggestions` — Get role suggestions from HR Agent

### Data Models

- **Organization**: contains `role_ids` (list of global role IDs), `input_role_id` (entry point for external prompts), status (draft/deployed/running/stopped)
- **Role**: global resource, has `soul_template`, `identity_template`, `context_memory`, `reports_to` (hierarchy), `hierarchy_level`, `permission_level`
- **DataFlow**: nodes (role/task/knowledge/input/output) + edges with `data_mapping` and optional conditions
- **Task**: belongs to organization, has `assigned_role_id`, `dependencies`, `prompt` field for workflow transformation

### OpenClaw Adapter

`api/services/openclaw_adapter.py` converts roles to OpenClaw Agent directories. Each deployed role gets:
- `SOUL.md` — from `role.soul_template`
- `IDENTITY.md` — from `role.identity_template`
- `AGENTS.md` — workspace config with knowledge base
- `skills/` — linked installed skills

### Frontend State

Zustand store (`web/src/stores/index.ts`) manages: organizations, roles, skills, loading states. API calls go through `web/src/services/api.ts`.

### Recent Additions (check git status for details)

- `api/routers/execution.py` + `web/src/services/executionApi.ts` — Workflow execution engine
- `api/routers/memory.py` — Context memory management
- `api/routers/agency.py` — agency-agents import functionality
- `api/routers/role_suggestions.py` + `web/src/services/roleSuggestionApi.ts` — HR Agent role suggestions
- `web/src/pages/ExecutionResult.tsx`, `MemoryManager.tsx` — New UI pages
- `api/services/memory_service.py`, `hr_agent_service.py`, `execution_service.py` — New backend services