import { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Select,
  Modal,
  Form,
  Input,
  message,
  Spin,
  List,
  Empty,
  Popconfirm,
  Alert
} from 'antd';
import {
  PlusOutlined,
  SyncOutlined,
  CompressOutlined,
  ReloadOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { memoryApi } from '../services/api';
import type { MemoryEntry, MemoryCompressionResponse, MemoryStats } from '../types';
import { useStore } from '../stores';
import MemoryCard from '../components/Memory/MemoryCard';
import MemoryStatsComponent from '../components/Memory/MemoryStats';
import CompressionModal from '../components/Memory/CompressionModal';

const { TextArea } = Input;

const MEMORY_TYPES = [
  { value: 'conversation', label: '对话' },
  { value: 'fact', label: '事实' },
  { value: 'preference', label: '偏好' },
  { value: 'context', label: '上下文' },
  { value: 'compressed', label: '已压缩' }
];

export default function MemoryManager() {
  const { roles, loadRoles } = useStore();
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isCompressionModalOpen, setIsCompressionModalOpen] = useState(false);
  const [editingMemory, setEditingMemory] = useState<MemoryEntry | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    loadRoles();
  }, [loadRoles]);

  useEffect(() => {
    if (roles.length > 0 && !selectedRoleId) {
      setSelectedRoleId(roles[0].id);
    }
  }, [roles, selectedRoleId]);

  useEffect(() => {
    if (selectedRoleId) {
      loadMemories(selectedRoleId);
      loadStats(selectedRoleId);
    }
  }, [selectedRoleId]);

  const loadMemories = async (roleId: string) => {
    setLoading(true);
    try {
      const data = await memoryApi.getRoleMemories(roleId);
      setMemories(data);
    } catch {
      message.error('加载记忆失败');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async (roleId: string) => {
    try {
      const data = await memoryApi.getMemoryStats(roleId);
      setStats(data);
    } catch {
      console.error('加载统计失败');
    }
  };

  const handleAddMemory = async (values: { content: string; memoryType: string }) => {
    if (!selectedRoleId) return;
    try {
      await memoryApi.addMemory(selectedRoleId, values.content);
      message.success('添加记忆成功');
      setIsAddModalOpen(false);
      form.resetFields();
      loadMemories(selectedRoleId);
      loadStats(selectedRoleId);
    } catch {
      message.error('添加记忆失败');
    }
  };

  const handleEditMemory = async (values: { content: string }) => {
    if (!selectedRoleId || !editingMemory) return;
    try {
      await memoryApi.updateMemory(selectedRoleId, editingMemory.id, values.content);
      message.success('更新记忆成功');
      setIsEditModalOpen(false);
      setEditingMemory(null);
      editForm.resetFields();
      loadMemories(selectedRoleId);
    } catch {
      message.error('更新记忆失败');
    }
  };

  const handleDeleteMemory = async (memoryId: string) => {
    if (!selectedRoleId) return;
    try {
      await memoryApi.deleteMemory(selectedRoleId, memoryId);
      message.success('删除记忆成功');
      loadMemories(selectedRoleId);
      loadStats(selectedRoleId);
    } catch {
      message.error('删除记忆失败');
    }
  };

  const handleAccessMemory = async (memoryId: string) => {
    if (!selectedRoleId) return;
    try {
      await memoryApi.accessMemory(selectedRoleId, memoryId);
      loadMemories(selectedRoleId);
    } catch {
      message.error('访问记忆失败');
    }
  };

  const handleCompress = async (maxEntries: number): Promise<MemoryCompressionResponse> => {
    if (!selectedRoleId) {
      throw new Error('请先选择角色');
    }
    const result = await memoryApi.compressMemories(selectedRoleId, maxEntries);
    message.success(`压缩完成: 保留 ${result.compressed_count} 条记忆`);
    loadMemories(selectedRoleId);
    loadStats(selectedRoleId);
    return result;
  };

  const handleSync = async () => {
    if (!selectedRoleId) return;
    try {
      await memoryApi.syncToOpenClaw(selectedRoleId);
      message.success('同步到 OpenClaw 成功');
    } catch {
      message.error('同步失败');
    }
  };

  const handleReset = async () => {
    if (!selectedRoleId) return;
    Modal.confirm({
      title: '确认重置记忆',
      content: '将清除除 FACT 和 PREFERENCE 类型外的所有记忆',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await fetch('/api/v1/memory/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              role_id: selectedRoleId,
              keep_types: ['fact', 'preference']
            })
          });
          if (response.ok) {
            message.success('重置成功');
            loadMemories(selectedRoleId);
            loadStats(selectedRoleId);
          }
        } catch {
          message.error('重置失败');
        }
      }
    });
  };

  const openEditModal = (memory: MemoryEntry) => {
    setEditingMemory(memory);
    editForm.setFieldsValue({ content: memory.content });
    setIsEditModalOpen(true);
  };

  const calculateImportance = (memory: MemoryEntry): number => {
    const typeWeights: Record<string, number> = {
      fact: 1.0,
      preference: 0.8,
      context: 0.6,
      conversation: 0.4,
      compressed: 0.2
    };

    const accessScore = Math.min(0.3, memory.access_count / 20);

    let recencyScore = 0.3;
    if (memory.last_accessed) {
      const hoursSince = (Date.now() - new Date(memory.last_accessed).getTime()) / 3600000;
      recencyScore = Math.max(0, 0.3 - (hoursSince / 168) * 0.3);
    }

    const typeScore = (typeWeights[memory.memory_type] || 0.4) * 0.3;
    const importanceScore = (memory.importance / 5) * 0.1;

    return accessScore + recencyScore + typeScore + importanceScore;
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>记忆管理</h2>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space>
              <span>选择角色:</span>
              <Select
                style={{ width: 200 }}
                placeholder="请选择角色"
                value={selectedRoleId}
                onChange={setSelectedRoleId}
                options={roles.map(r => ({ value: r.id, label: r.name }))}
              />
              <Button
                icon={<ReloadOutlined />}
                onClick={() => selectedRoleId && loadMemories(selectedRoleId)}
              >
                刷新
              </Button>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setIsAddModalOpen(true)}
              >
                添加记忆
              </Button>
              <Button
                icon={<CompressOutlined />}
                onClick={() => setIsCompressionModalOpen(true)}
              >
                压缩
              </Button>
              <Popconfirm
                title="确认重置记忆?"
                description="将清除非关键类型记忆"
                onConfirm={handleReset}
                okText="确认"
                cancelText="取消"
              >
                <Button icon={<DeleteOutlined />}>重置</Button>
              </Popconfirm>
              <Button
                icon={<SyncOutlined />}
                onClick={handleSync}
              >
                同步到 OpenClaw
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col span={16}>
          <Card title="记忆列表">
            {loading ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin />
              </div>
            ) : memories.length === 0 ? (
              <Empty description="暂无记忆" />
            ) : (
              <List
                dataSource={memories}
                renderItem={(memory) => (
                  <MemoryCard
                    key={memory.id}
                    memory={memory}
                    importance={calculateImportance(memory)}
                    onEdit={openEditModal}
                    onDelete={handleDeleteMemory}
                    onAccess={handleAccessMemory}
                  />
                )}
              />
            )}
          </Card>
        </Col>

        <Col span={8}>
          <MemoryStatsComponent stats={stats} />

          <Alert
            message="重要性计算说明"
            description="重要性 = 访问频率(0.3) + 时间衰减(0.3) + 类型权重(0.3) + 用户标记(0.1)"
            type="info"
            style={{ marginTop: 16 }}
            showIcon
          />
        </Col>
      </Row>

      <Modal
        title="添加记忆"
        open={isAddModalOpen}
        onCancel={() => {
          setIsAddModalOpen(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddMemory}
        >
          <Form.Item
            name="memoryType"
            label="记忆类型"
            initialValue="conversation"
          >
            <Select options={MEMORY_TYPES} />
          </Form.Item>
          <Form.Item
            name="content"
            label="记忆内容"
            rules={[{ required: true, message: '请输入记忆内容' }]}
          >
            <TextArea rows={4} placeholder="输入记忆内容..." />
          </Form.Item>
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsAddModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit">添加</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑记忆"
        open={isEditModalOpen}
        onCancel={() => {
          setIsEditModalOpen(false);
          setEditingMemory(null);
          editForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditMemory}
        >
          <Form.Item
            name="content"
            label="记忆内容"
            rules={[{ required: true, message: '请输入记忆内容' }]}
          >
            <TextArea rows={4} placeholder="输入记忆内容..." />
          </Form.Item>
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsEditModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit">保存</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <CompressionModal
        open={isCompressionModalOpen}
        onCancel={() => setIsCompressionModalOpen(false)}
        roleId={selectedRoleId || ''}
        onConfirm={handleCompress}
      />
    </div>
  );
}
