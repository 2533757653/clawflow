# ClawFlow 🐙

**Multi-Agent Workflow Orchestrator for OpenClaw**

![ClawFlow Web UI](Picture.png)

## Core Philosophy

**Automated closed-loop from Idea to Production**

```
Idea → Requirement → Planning → Review → Execution → Deployment → Documentation
```

## Quick Start

```bash
# Install
pip install clawflow

# Initialize project
clawflow init my-project

# Run workflow
clawflow run claw.yaml

# Start Web UI
clawflow webui --port 8766
```

## Architecture

```
┌─────────────────────────────────────────┐
│  YAML Configuration (claw.yaml)         │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  Orchestration Engine (clawflow core)   │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  OpenClaw Runtime                       │
└─────────────────────────────────────────┘
```

## Key Features

### 🔄 Message-Driven Communication

Agents communicate via message bus, not direct calls:

```python
# Send task
message_bus.send("code_worker", task_message)

# Receive response
response = message_bus.receive("orchestrator", timeout=30)
```

### 🚀 Self-Bootstrapping

ClawFlow creates its own agents at startup:

```
Meta-Agent → Worker-Builder → data/code/doc/workers
```

### 🔁 Self-Update Mechanism

ClawFlow can update itself using its own workflow engine:

```yaml
# self-update.yaml
agents:
  - router
  - planner
  - code_worker
  - deploy_worker

workflow:
  entry: router
  steps:
    - router → planner → code_worker → deploy_worker
```

### 🔌 OpenClaw Integration

```bash
# Install skill
clawhub install clawflow

# Use in OpenClaw
clawflow run "Create a data analysis feature"
```

### 🌐 Web UI

Access the Web UI at `http://localhost:8766` for:
- Real-time system status dashboard
- Active agents monitoring
- Workflow execution interface
- Template marketplace browser
- Execution logs

## Built-in Agents

| Agent | Type | Responsibility |
|-------|------|----------------|
| `meta_agent` | Meta | Create and manage other agents |
| `worker_builder` | Builder | Generate workers from templates |
| `router` | Router | Entry point, filter requirements |
| `planner` | Planner | Task planning and decomposition |
| `reviewer` | Reviewer | Feasibility review |
| `orchestrator` | Orchestrator | Task dispatch and result aggregation |
| `data_worker` | Worker | Data processing |
| `code_worker` | Worker | Code implementation |
| `doc_worker` | Worker | Documentation generation |
| `review_worker` | Worker | Quality assurance |

## API

### HTTP Endpoints

```bash
# Run workflow
curl -X POST http://localhost:8765/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Create a feature"}'

# Check status
curl http://localhost:8765/status

# List agents
curl http://localhost:8765/agents

# Create custom agent
curl -X POST http://localhost:8765/agents/create \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_agent",
    "type": "Worker",
    "capabilities": ["exec", "web_search"]
  }'

# Web UI API
curl http://localhost:8766/api/templates
curl http://localhost:8766/api/status
```

## Project Structure

```
clawflow/
├── src/clawflow/
│   ├── __init__.py
│   ├── engine.py         # Workflow engine
│   ├── agents.py         # Agent implementations
│   ├── workflow.py       # Workflow definitions
│   ├── message_bus.py    # Message bus (async communication)
│   ├── agent_base.py     # Agent base classes
│   ├── server.py         # Independent HTTP service
│   ├── cli.py            # Command-line interface
│   └── webui/
│       ├── app.py        # Web UI Flask backend
│       └── templates/
│           └── index.html # Web UI frontend
├── templates/            # Pre-built workflow templates
│   ├── quant-strategy.yaml
│   ├── code-dev.yaml
│   ├── data-analysis.yaml
│   ├── research-paper.yaml
│   ├── self-update.yaml
│   └── README.md
├── examples/
│   └── claw.yaml         # Example workflow
├── self-update.yaml      # Self-update workflow
├── skills/
│   └── clawflow-skill/
│       └── SKILL.md      # OpenClaw skill definition
├── pyproject.toml
├── setup.py
└── README.md
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Install Web UI dependencies
pip install -e ".[webui]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## Roadmap

### ✅ Completed (v0.1.0)
- [x] Message bus (in-memory)
- [x] Self-bootstrapping agents
- [x] HTTP API
- [x] Web UI (workflow visualization)
- [x] Template marketplace (5 pre-built workflows)

### 🚧 In Progress (v0.2.0)
- [ ] Redis message bus (production-ready)
- [ ] WebSocket real-time updates
- [ ] Complete workflow execution logic
- [ ] Agent message handling

### 📋 Planned (v0.3.0+)
- [ ] Distributed deployment (Kubernetes)
- [ ] Template marketplace (community contributions)
- [ ] Workflow editor (drag-and-drop)
- [ ] Advanced monitoring (Prometheus/Grafana)

## License

MIT
