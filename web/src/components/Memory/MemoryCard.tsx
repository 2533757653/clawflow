import { Card, Tag, Space, Button, Popconfirm, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import type { MemoryEntry } from '../../types';

interface MemoryCardProps {
  memory: MemoryEntry;
  importance: number;
  onEdit: (memory: MemoryEntry) => void;
  onDelete: (memoryId: string) => void;
  onAccess: (memoryId: string) => void;
}

const typeColors: Record<string, string> = {
  conversation: 'blue',
  fact: 'green',
  preference: 'orange',
  context: 'purple',
  compressed: 'gray'
};

export default function MemoryCard({
  memory,
  importance,
  onEdit,
  onDelete,
  onAccess
}: MemoryCardProps) {
  const typeColor = typeColors[memory.memory_type] || 'default';

  return (
    <Card
      size="small"
      style={{ marginBottom: 8 }}
      title={
        <Space>
          <Tag color={typeColor}>{memory.memory_type}</Tag>
          <Tooltip title={`重要性: ${importance.toFixed(2)}`}>
            <span style={{ fontSize: 12, color: '#888' }}>
              ⭐ {importance.toFixed(2)}
            </span>
          </Tooltip>
        </Space>
      }
      extra={
        <Space size="small">
          <Tooltip title="查看并增加访问次数">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onAccess(memory.id)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => onEdit(memory)}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除这条记忆?"
            onConfirm={() => onDelete(memory.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      }
    >
      <div style={{ marginBottom: 8 }}>
        {memory.content}
      </div>
      <div style={{ fontSize: 11, color: '#999' }}>
        <Space split="|">
          <span>创建: {new Date(memory.created_at).toLocaleString()}</span>
          {memory.last_accessed && (
            <span>访问: {new Date(memory.last_accessed).toLocaleString()}</span>
          )}
          <span>访问次数: {memory.access_count}</span>
        </Space>
      </div>
      {memory.tags && memory.tags.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {memory.tags.map(tag => (
            <Tag key={tag} style={{ fontSize: 12 }}>{tag}</Tag>
          ))}
        </div>
      )}
    </Card>
  );
}
