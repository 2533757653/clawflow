#!/usr/bin/env python3
"""
运行集成版 ClawFlow 服务

此版本利用 OpenClaw 原生 Agent 系统并内置 Actor-Critic 引擎
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clawflow.integrated_server import main

if __name__ == "__main__":
    main()