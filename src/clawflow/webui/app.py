"""
ClawFlow Web UI - Flask Backend

提供工作流可视化、Agent 状态、模板市场等功能的后端 API
"""

import json
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import requests

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'clawflow-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# ClawFlow 服务地址
CLAWFLOW_SERVICE_URL = os.environ.get('CLAWFLOW_SERVICE_URL', 'http://localhost:8765')

# 模板目录（指向项目根目录的 templates 文件夹）
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / 'templates'


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """获取 ClawFlow 服务状态"""
    try:
        resp = requests.get(f'{CLAWFLOW_SERVICE_URL}/status', timeout=5)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'disconnected'}), 500


@app.route('/api/agents')
def get_agents():
    """获取所有 Agents"""
    try:
        resp = requests.get(f'{CLAWFLOW_SERVICE_URL}/agents', timeout=5)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/templates')
def list_templates():
    """列出所有可用模板"""
    templates = []
    if TEMPLATES_DIR.exists():
        for f in TEMPLATES_DIR.glob('*.yaml'):
            try:
                content = f.read_text()
                # 简单解析 YAML 获取元数据
                name = f.stem
                description = ""
                for line in content.split('\n')[:10]:
                    if line.startswith('description:'):
                        description = line.split(':', 1)[1].strip().strip('"')
                        break
                templates.append({
                    'id': name,
                    'name': name.replace('-', ' ').title(),
                    'description': description,
                    'file': f.name,
                })
            except Exception:
                pass
    return jsonify(templates)


@app.route('/api/templates/<template_id>')
def get_template(template_id):
    """获取模板详情"""
    template_path = TEMPLATES_DIR / f'{template_id}.yaml'
    if template_path.exists():
        return jsonify({
            'id': template_id,
            'content': template_path.read_text(),
        })
    return jsonify({'error': 'Template not found'}), 404


@app.route('/api/run', methods=['POST'])
def run_workflow():
    """运行工作流"""
    data = request.json
    try:
        resp = requests.post(
            f'{CLAWFLOW_SERVICE_URL}/run',
            json=data,
            timeout=10,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/create', methods=['POST'])
def create_agent():
    """创建新 Agent"""
    data = request.json
    try:
        resp = requests.post(
            f'{CLAWFLOW_SERVICE_URL}/agents/create',
            json=data,
            timeout=10,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('Client connected')
    emit('connected', {'message': 'Connected to ClawFlow Web UI'})


@socketio.on('subscribe')
def handle_subscribe(data):
    """订阅 Agent 状态更新"""
    agent_id = data.get('agent_id')
    if agent_id:
        # 可以在这里添加订阅逻辑
        emit('subscribed', {'agent_id': agent_id})


def broadcast_agent_update(agent_id: str, status: dict):
    """广播 Agent 状态更新"""
    socketio.emit('agent_update', {
        'agent_id': agent_id,
        'status': status,
    })


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8766, debug=True, allow_unsafe_werkzeug=True)
