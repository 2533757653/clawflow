# ClawFlow Prompts Index

This directory contains detailed implementation prompts for each feature module of the ClawFlow project.

## Prompt Files

| # | File | Description | Priority |
|---|------|-------------|----------|
| 1 | [workflow-execution-engine.md](./workflow-execution-engine.md) | Workflow execution engine combining DataFlow and Tasks | 🔴 High |
| 2 | [input-role-trigger.md](./input-role-trigger.md) | Input role triggering mechanism for user interactions | 🔴 High |
| 3 | [memory-compression.md](./memory-compression.md) | Context memory compression system | 🟡 Medium |
| 4 | [rag-knowledge-base.md](./rag-knowledge-base.md) | RAG-based knowledge database | 🟡 Medium |
| 5 | [hr-agent-responsibilities.md](./hr-agent-responsibilities.md) | HR Agent for auto-filling role responsibilities | 🟢 Low |
| 6 | [dataflow-visualization.md](./dataflow-visualization.md) | Frontend DataFlow visualization enhancements | 🟢 Low |
| 7 | [api-testing.md](./api-testing.md) | API test coverage | 🟢 Low |

## Usage

Each prompt file contains:
- **Project Context**: Architecture and existing implementations
- **Design Decisions**: From SPEC.md discussions
- **Task Requirements**: Detailed implementation steps
- **Code Examples**: Templates and structures
- **File Structure**: Expected new/modified files
- **Acceptance Criteria**: Definition of done

## Execution Order

Recommended execution order for parallel agents:

```
Phase 1 (High Priority - Core Functionality):
├── Agent 1: workflow-execution-engine.md
└── Agent 2: input-role-trigger.md

Phase 2 (Medium Priority - Data Management):
├── Agent 3: memory-compression.md
└── Agent 4: rag-knowledge-base.md

Phase 3 (Low Priority - Enhancement):
├── Agent 5: hr-agent-responsibilities.md
├── Agent 6: dataflow-visualization.md
└── Agent 7: api-testing.md
```

## Project Reference

- **Project Root**: `d:\clawflow`
- **Backend**: `api/` (FastAPI + Python 3.11+)
- **Frontend**: `web/` (React 18 + TypeScript)
- **Spec**: `SPEC.md`
- **Architecture**: `docs/architecture.md`

## Key Models

See `api/models/__init__.py` for:
- `Organization` - with `role_ids` field
- `Role` - global resource
- `Task` - with `assigned_role_id`
- `DataFlow` - with nodes and edges
- `Knowledge` - organization-level

## Key Services

See `api/services/`:
- `storage.py` - JSON file storage
- `openclaw_adapter.py` - OpenClaw deployment
- `rag_service.py` - RAG operations
- `memory_service.py` - Memory operations (partial)
