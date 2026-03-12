# ClawFlow 🐙

OpenClaw 多智能体工作流编排引擎

## 核心理念

**从想法到产品落地的自动化闭环**

```
想法 → 需求 → 规划 → 审核 → 执行 → 部署 → 文档
```

## 快速开始

```bash
# 安装
pip install clawflow

# 初始化项目
clawflow init my-project

# 运行工作流
clawflow run claw.yaml
```

## 架构

```
┌─────────────────────────────────────────┐
│  YAML 配置层 (claw.yaml)                │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  编排引擎 (clawflow core)               │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  OpenClaw Runtime                       │
└─────────────────────────────────────────┘
```

## 自更新机制

ClawFlow 支持**自举更新**：框架可以通过自身的工作流引擎来更新自身。

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

## License

MIT
