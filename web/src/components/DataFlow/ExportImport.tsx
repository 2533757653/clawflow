import { Button, message } from 'antd';
import { UploadOutlined, DownloadOutlined } from '@ant-design/icons';
import { Node, Edge } from '@xyflow/react';

interface FlowNodeData extends Record<string, unknown> {
  label: string;
  nodeType: string;
  refId?: string;
}

interface ExportImportProps {
  nodes: Node<FlowNodeData>[];
  edges: Edge[];
  onImport: (nodes: Node<FlowNodeData>[], edges: Edge[]) => void;
}

export const ExportImport: React.FC<ExportImportProps> = ({ nodes, edges, onImport }) => {
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
          onImport(data.nodes, data.edges);
          message.success('数据流导入成功');
        }
      } catch {
        message.error('文件格式错误');
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  return (
    <div>
      <Button icon={<DownloadOutlined />} onClick={handleExport} style={{ marginRight: 8 }}>
        导出
      </Button>
      <Button icon={<UploadOutlined />}>
        导入
        <input
          type="file"
          accept=".json"
          onChange={handleImport}
          style={{ position: 'absolute', left: 0, opacity: 0, width: '100%', height: '100%', cursor: 'pointer' }}
        />
      </Button>
    </div>
  );
};