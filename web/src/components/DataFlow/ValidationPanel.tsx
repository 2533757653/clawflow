import { Alert, List, Tag, Space } from 'antd';
import { WarningOutlined, CloseCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';
import type { DataFlowNode, DataFlowEdge } from '../../types';

interface ValidationResult {
  type: 'error' | 'warning' | 'info';
  message: string;
  nodeId?: string;
}

interface ValidationPanelProps {
  nodes: DataFlowNode[];
  edges: DataFlowEdge[];
}

const validateDataflow = (nodes: DataFlowNode[], edges: DataFlowEdge[]): ValidationResult[] => {
  const results: ValidationResult[] = [];

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

  nodes.forEach(n => {
    if (['role', 'task', 'knowledge'].includes(n.type) && !n.ref_id) {
      results.push({
        type: 'warning',
        message: `节点 "${n.label}" 未关联实体`,
        nodeId: n.id
      });
    }
  });

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

const getIcon = (type: 'error' | 'warning' | 'info') => {
  switch (type) {
    case 'error':
      return <CloseCircleOutlined />;
    case 'warning':
      return <WarningOutlined />;
    case 'info':
      return <InfoCircleOutlined />;
  }
};

const getColor = (type: 'error' | 'warning' | 'info') => {
  switch (type) {
    case 'error':
      return 'error';
    case 'warning':
      return 'warning';
    case 'info':
      return 'info';
  }
};

export const ValidationPanel: React.FC<ValidationPanelProps> = ({ nodes, edges }) => {
  const results = validateDataflow(nodes, edges);

  if (results.length === 0) {
    return (
      <Alert
        message="验证通过"
        description="数据流没有发现问题"
        type="success"
        showIcon
      />
    );
  }

  return (
    <List
      size="small"
      header={<Space><span>验证结果</span><Tag>{results.length}</Tag></Space>}
      dataSource={results}
      renderItem={(item) => (
        <Alert
          message={item.message}
          type={getColor(item.type)}
          showIcon
          icon={getIcon(item.type)}
          style={{ marginBottom: 8 }}
        />
      )}
    />
  );
};