# ClawFlow Template Marketplace

Pre-built workflow templates for common use cases.

## Available Templates

### 📈 Quantitative Strategy (`quant-strategy.yaml`)
From idea to deployment for quantitative trading strategies.

**Workflow**: Router → Planner → Data Worker → Code Worker → Review → Deploy

**Example Use**:
```
Develop a dual moving average crossover strategy:
- Short MA: 5 days
- Long MA: 20 days
- Assets: CSI 300 components
- Backtest period: 2020-2024
```

---

### 💻 Code Development (`code-dev.yaml`)
Complete development flow from requirement to production.

**Workflow**: Router → Planner → Code → Review → Docs → Deploy

**Example Use**:
```
Create a RESTful API endpoint:
- Function: User data query
- Path: GET /api/users/{id}
- Auth: JWT Token
- Test coverage: >80%
```

---

### 📊 Data Analysis (`data-analysis.yaml`)
From data to insights analysis pipeline.

**Workflow**: Router → Planner → Data → Code → Docs

**Example Use**:
```
Analyze e-commerce sales data:
- Source: MySQL database sales_db
- Dimensions: time, category, region
- Visualizations: trends, heatmaps, funnels
- Output: PDF report + Jupyter Notebook
```

---

### 📝 Research Paper (`research-paper.yaml`)
From topic to publication research workflow.

**Workflow**: Router → Planner → Data → Code → Docs → Review

**Example Use**:
```
Write a deep learning paper:
- Topic: Transformer in time series forecasting
- Datasets: power load, stock prices
- Baselines: LSTM, GRU, ARIMA
- Target: NeurIPS / ICML
```

---

### 🔄 Self-Update (`self-update.yaml`)
ClawFlow framework self-bootstrapping update.

**Workflow**: Router → Planner → Code → Review → Deploy

**Features**:
- Auto backup before update
- Rollback on failure
- Version verification

---

## Using Templates

### Via CLI
```bash
# List templates
clawflow templates list

# Run with template
clawflow run --template quant-strategy
```

### Via Web UI
1. Open http://localhost:8766
2. Browse Template Marketplace
3. Click a template to use it
4. Customize the input and run

### Via API
```bash
curl -X POST http://localhost:8765/run \
  -H "Content-Type: application/json" \
  -d '{
    "template": "quant-strategy",
    "input": "Develop a momentum strategy"
  }'
```

## Creating Custom Templates

1. Copy an existing template:
   ```bash
   cp templates/quant-strategy.yaml templates/my-workflow.yaml
   ```

2. Edit the template:
   - Change `name`, `description`
   - Define your agents
   - Set up workflow steps

3. Test your template:
   ```bash
   clawflow run templates/my-workflow.yaml
   ```

4. Share with community (optional):
   - Submit a PR to the ClawFlow repo
   - Publish to template marketplace

## Template Schema

```yaml
name: <template-id>
description: "<Human-readable description>"
version: "<semver>"

agents:
  <agent_id>:
    type: <Router|Planner|Worker|...>
    description: "<What this agent does>"
    capabilities: ["exec", "web_fetch", ...]

workflow:
  entry: <entry_agent_id>
  steps:
    - from: <agent_id>
      condition: <condition_name>
      to: <next_agent_id>

example_input: |
  <Example user input for this template>
```

## Contributing

Contributions welcome! Please:
1. Follow the schema above
2. Include clear `description` and `example_input`
3. Test your template before submitting
4. Add documentation in this README
