# Prompt: 前端数据流可视化增强

## 项目信息

- **项目名称**: ClawFlow - Agent 组织动态构建平台
- **项目路径**: `d:\clawflow`
- **后端**: `api/` (FastAPI + Python 3.11+)
- **前端**: `web/` (React 18 + TypeScript)

## 项目架构

参见 `docs/prompts/workflow-execution-engine.md`

## 已有实现

### DataFlowEditor 页面 (已有基础)
位置: `web/src/pages/DataFlowEditor.tsx`

当前功能:
- 数据流列表展示
- 创建数据流
- ReactFlow 设计器
- 节点类型: role, task, knowledge, input, output
- 节点颜色编码
- 添加节点
- 节点连线

### 当前模型
```typescript
interface FlowNodeData {
  label: string
  nodeType: string
  refId?: string
}
```

## 任务要求

### 1. 安装依赖

```bash
cd web
npm install @xyflow/react dagre @types/dagre
```

### 2. 节点可视化增强

修改 `web/src/pages/DataFlowEditor.tsx`:

```typescript
// 节点图标映射
const nodeIcons: Record<string, ReactNode> = {
  role: <TeamOutlined />,
  task: <CheckSquareOutlined />,
  knowledge: <DatabaseOutlined />,
  input: <ArrowDownOutlined />,
  output: <ArrowUpOutlined />
}

// 节点样式增强
const getNodeStyle = (node: DataFlowNode, role?: Role, task?: Task) => {
  const baseStyle = {
    background: nodeColors[node.type],
    color: 'white',
    border: `2px solid ${nodeColors[node.type]}`,
    borderRadius: 8,
    padding: '10px 20px',
    minWidth: 150,
  };

  return (
    <div style={baseStyle}>
      <Space>
        <Tag icon={nodeIcons[node.type]} style={{ margin: 0 }}>
          {node.type.toUpperCase()}
        </Tag>
      </Space>
      <div style={{ marginTop: 8, fontWeight: 'bold' }}>
        {node.label || (role?.name || task?.name || node.type)}
      </div>
      {node.ref_id && (
        <Tag color="green" style={{ marginTop: 4 }}>
          已关联
        </Tag>
      )}
      {!node.ref_id && node.type !== 'input' && node.type !== 'output' && (
        <Tag color="orange" style={{ marginTop: 4 }}>
          未关联
        </Tag>
      )}
    </div>
  );
};
```

### 3. 添加 MiniMap

```typescript
import { MiniMap } from '@xyflow/react';

<ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onConnect={onConnect}
  onNodeClick={handleNodeClick}
>
  <Background />
  <MiniMap
    nodeColor={(node) => nodeColors[node.data?.nodeType] || '#999'}
    maskColor="rgb(240, 240, 240, 0.8)"
    style={{
      width: 150,
      height: 100,
    }}
  />
</ReactFlow>
```

### 4. 添加 Controls

```typescript
import { Controls } from '@xyflow/react';

<ReactFlow ...>
  <Controls />
  <MiniMap ... />
  <Background />
</ReactFlow>
```

### 5. 节点 Context Menu

创建 `web/src/components/DataFlow/NodeContextMenu.tsx`:

```typescript
import { Menu, Modal } from 'antd';
import { EditOutlined, CopyOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';

interface NodeContextMenuProps {
  node: DataFlowNode;
  position: { x: number; y: number };
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onViewDetails: () => void;
}

export const NodeContextMenu: React.FC<NodeContextMenuProps> = ({
  node,
  position,
  onEdit,
  onDuplicate,
  onDelete,
  onViewDetails
}) => {
  const [contextMenuVisible, setContextMenuVisible] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState(position);

  const handleContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    setContextMenuPosition({ x: event.clientX, y: event.clientY });
    setContextMenuVisible(true);
  };

  const menuItems = [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑节点',
      onClick: onEdit
    },
    {
      key: 'view',
      icon: <EyeOutlined />,
      label: '查看详情',
      onClick: onViewDetails
    },
    {
      key: 'duplicate',
      icon: <CopyOutlined />,
      label: '复制节点',
      onClick: onDuplicate
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除节点',
      danger: true,
      onClick: onDelete
    }
  ];

  return (
    <>
      <div onContextMenu={handleContextMenu}>
        {/* 节点内容 */}
      </div>
      <Menu
        items={menuItems}
        onClick={({ key }) => {
          setContextMenuVisible(false);
          switch (key) {
            case 'edit': onEdit(); break;
            case 'duplicate': onDuplicate(); break;
            case 'delete': onDelete(); break;
            case 'view': onViewDetails(); break;
          }
        }}
        open={contextMenuVisible}
        onOpenChange={(open) => setContextMenuVisible(open)}
        style={{ position: 'fixed', left: contextMenuPosition.x, top: contextMenuPosition.y }}
      />
    </>
  );
};
```

### 6. 边标签显示

```typescript
// 在 Edge 上显示 data_mapping 标签
const EdgeWithLabel = ({ id, source, target, label, dataMapping }) => {
  return (
    <>
      <Edge
        id={id}
        source={source}
        target={target}
        label={label || (dataMapping ? Object.keys(dataMapping).join(', ') : null)}
        style={{ fontSize: 10 }}
      />
    </>
  );
};

// 自定义边组件
const CustomEdge = (props: any) => {
  const { id, source, target, label, data } = props;
  const mappingText = data?.dataMapping
    ? Object.entries(data.dataMapping).map(([k]) => k).join(' → ')
    : '';

  return (
    <>
      <BaseEdge {...props} />
      <EdgeLabel
        {...props}
        label={label || mappingText}
        style={{
          position: 'absolute',
          transform: `translate(-50%, -50%)`,
          fontSize: 10,
          pointerEvents: 'all',
        }}
      />
    </>
  );
};
```

### 7. 自动布局

创建 `web/src/components/DataFlow/AutoLayoutButton.tsx`:

```typescript
import dagre from 'dagre';

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 172;
  const nodeHeight = 60;

  dagreGraph.setGraph({
    rankdir: 'TB',  // Top to Bottom
    nodesep: 50,
    ranksep: 80
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

// 使用
const handleAutoLayout = () => {
  const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(nodes, edges);
  setNodes(layoutedNodes);
  setEdges(layoutedEdges);
  message.success('已自动排列布局');
};
```

### 8. 验证面板

创建 `web/src/components/DataFlow/ValidationPanel.tsx`:

```typescript
interface ValidationResult {
  type: 'error' | 'warning' | 'info';
  message: string;
  nodeId?: string;
}

const validateDataflow = (nodes: DataFlowNode[], edges: DataFlowEdge[]): ValidationResult[] => {
  const results: ValidationResult[] = [];

  // 检查孤立节点
  const connectedNodes = new Set<string>();
  edges.forEach(e => {
    connectedNodes.add(e.source);
    connectedNodes.add(e.target);
  });

  nodes.forEach(n => {
    if (n.type !== 'input' && n.type !== 'output' && !connectedNodes.has(n.id)) {
      results.push({
        type: 'warning',
        message: `节点 "${n.label}" 未连接`,
        nodeId: n.id
      });
    }
  });

  // 检查无 ref_id 的节点
  nodes.forEach(n => {
    if (['role', 'task', 'knowledge'].includes(n.type) && !n.ref_id) {
      results.push({
        type: 'warning',
        message: `节点 "${n.label}" 未关联实体`,
        nodeId: n.id
      });
    }
  });

  // 检查循环引用
  const visited = new Set<string>();
  const recStack = new Set<string>();

  const hasCycle = (nodeId: string): boolean => {
    visited.add(nodeId);
    recStack.add(nodeId);

    const outgoing = edges.filter(e => e.source === nodeId);
    for (const edge of outgoing) {
      if (!visited.has(edge.target)) {
        if (hasCycle(edge.target)) return true;
      } else if (recStack.has(edge.target)) {
        return true;
      }
    }

    recStack.delete(nodeId);
    return false;
  };

  nodes.forEach(n => {
    if (!visited.has(n.id) && hasCycle(n.id)) {
      results.push({
        type: 'error',
        message: '检测到循环引用'
      });
    }
  });

  return results;
};
```

### 9. 导出/导入

```typescript
const handleExport = () => {
  const dataflowJson = JSON.stringify({ nodes, edges }, null, 2);
  const blob = new Blob([dataflowJson], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `dataflow-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target?.result as string);
      if (data.nodes && data.edges) {
        setNodes(data.nodes);
        setEdges(data.edges);
        message.success('数据流导入成功');
      }
    } catch {
      message.error('文件格式错误');
    }
  };
  reader.readAsText(file);
};
```

## 文件结构

```
web/src/
├── components/
│   └── DataFlow/
│       ├── NodeContextMenu.tsx
│       ├── AutoLayoutButton.tsx
│       ├── ValidationPanel.tsx
│       ├── EdgeWithLabel.tsx
│       └── ExportImport.tsx
└── pages/
    └── DataFlowEditor.tsx  # 修改: 集成所有增强
```

## 注意事项

1. **ReactFlow 版本**: 使用 `@xyflow/react` (React Flow v11+)
2. **布局算法**: dagre 适合有向无环图
3. **性能**: 大量节点时考虑虚拟化
4. **响应式**: 支持触摸操作

## 验收标准

- [ ] MiniMap 显示在右下角
- [ ] Controls 显示缩放和适应按钮
- [ ] 右键节点显示上下文菜单
- [ ] 边显示 data_mapping 标签
- [ ] 自动布局按钮工作正常
- [ ] 验证面板显示问题和警告
- [ ] 可以导出数据流为 JSON
- [ ] 可以导入数据流 JSON
