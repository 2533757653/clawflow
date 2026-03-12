"""
命令行接口

clawflow init <project-name>
clawflow run <config.yaml>
clawflow status
"""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .engine import WorkflowEngine

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """ClawFlow - OpenClaw 多智能体工作流编排引擎"""
    pass


@main.command()
@click.argument('project_name')
def init(project_name: str):
    """初始化新项目"""
    project_dir = Path(project_name)
    
    if project_dir.exists():
        console.print(f"[red]目录 {project_name} 已存在[/red]")
        return
    
    # 创建项目结构
    project_dir.mkdir(parents=True)
    (project_dir / "workflows").mkdir()
    (project_dir / "agents").mkdir()
    (project_dir / "output").mkdir()
    
    # 创建默认配置文件
    default_config = """# ClawFlow 配置文件
version: "1.0"

agents:
  router:
    type: Router
    description: "入口路由器"
    tools:
      - "memory_search"
    rules:
      - "只转发明确的项目需求"

  planner:
    type: Planner
    description: "任务规划器"
    tools:
      - "memory_search"
      - "web_search"
    rules:
      - "任务分解要具体、可衡量"

  orchestrator:
    type: Orchestrator
    description: "任务调度器"
    tools:
      - "sessions_spawn"
      - "subagents"
    rules:
      - "按任务类型分发到对应 worker"

workflow:
  entry: "router"
  steps:
    - from: "router"
      condition: "valid_requirement"
      to: "planner"
    
    - from: "planner"
      condition: "plan_created"
      to: "orchestrator"
    
    - from: "orchestrator"
      condition: "all_tasks_completed"
      to: "router"
"""
    
    (project_dir / "claw.yaml").write_text(default_config)
    
    console.print(Panel.fit(
        f"[green]✓[/green] 项目 {project_name} 初始化完成\n\n"
        f"目录结构:\n"
        f"  {project_name}/\n"
        f"  ├── claw.yaml      # 工作流配置\n"
        f"  ├── workflows/     # 工作流定义\n"
        f"  ├── agents/        # 自定义 Agent\n"
        f"  └── output/        # 执行结果\n\n"
        f"运行：[bold]clawflow run {project_name}/claw.yaml[/bold]",
        title="🐙 ClawFlow",
    ))


@main.command()
@click.argument('config_path', type=click.Path(exists=True))
@click.option('--input', '-i', 'user_input', default="创建一个数据分析功能", help="用户输入")
def run(config_path: str, user_input: str):
    """运行工作流"""
    console.print(f"[blue]加载配置：{config_path}[/blue]")
    
    try:
        engine = WorkflowEngine(config_path)
        console.print(f"[green]✓[/green] 加载 {len(engine.agents)} 个 Agent")
        
        console.print(f"\n[bold]执行工作流...[/bold]\n")
        result = engine.run(user_input)
        
        console.print(Panel(
            f"[green]✓[/green] 工作流执行完成\n\n"
            f"结果：{result}",
            title="执行结果",
        ))
        
    except Exception as e:
        console.print(f"[red]✗ 执行失败：{e}[/red]")
        raise


@main.command()
def status():
    """显示系统状态"""
    console.print(Panel(
        "[bold]ClawFlow 状态[/bold]\n\n"
        "版本：0.1.0\n"
        "状态：运行中\n"
        "OpenClaw: 已连接",
        title="📊 系统状态",
    ))


@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind')
@click.option('--port', type=int, default=8766, help='Port to bind')
def webui(host: str, port: int):
    """启动 Web UI"""
    try:
        from clawflow.webui.app import socketio, app
        console.print(f"[blue]启动 Web UI：http://{host}:{port}[/blue]")
        console.print(f"[dim]模板目录：/root/Agents/Profession/clawflow/templates[/dim]")
        socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
    except ImportError as e:
        console.print(f"[red]Web UI 启动失败：{e}[/red]")
        console.print("[dim]尝试运行：pip install flask flask-socketio requests[/dim]")


if __name__ == "__main__":
    main()
