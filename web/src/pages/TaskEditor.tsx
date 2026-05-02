import { Card, Table, Button, Space, Tag, Modal, Form, Input, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useStore } from '../stores'
import type { Task } from '../types'

const { TextArea } = Input

const priorityColors: Record<string, string> = {
  high: 'red',
  medium: 'orange',
  low: 'green'
}

export default function TaskEditor() {
  const {
    currentOrganizationId,
    tasks,
    roles,
    loadTasks,
    createTask,
    updateTask,
    deleteTask,
    loadRoles,
    loading
  } = useStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    if (currentOrganizationId) {
      loadTasks(currentOrganizationId)
      loadRoles()
    }
  }, [currentOrganizationId, loadTasks, loadRoles])

  const handleCreate = async (values: Partial<Task>) => {
    if (!currentOrganizationId) {
      message.warning('请先选择一个组织')
      return
    }
    try {
      await createTask(currentOrganizationId, values)
      message.success('任务创建成功')
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      message.error('创建失败')
    }
  }

  const handleUpdate = async (values: Partial<Task>) => {
    if (!currentOrganizationId || !editingTask) return
    try {
      await updateTask(currentOrganizationId, editingTask.id, values)
      message.success('任务更新成功')
      setIsModalOpen(false)
      setEditingTask(null)
      form.resetFields()
    } catch {
      message.error('更新失败')
    }
  }

  const handleDelete = async (taskId: string) => {
    if (!currentOrganizationId) return
    try {
      await deleteTask(currentOrganizationId, taskId)
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  const openEditModal = (task: Task) => {
    setEditingTask(task)
    form.setFieldsValue({
      ...task,
      dependencies: task.dependencies || []
    })
    setIsModalOpen(true)
  }

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => (
        <Tag color={priorityColors[priority]}>{priority.toUpperCase()}</Tag>
      )
    },
    {
      title: '执行模式',
      dataIndex: 'execution_mode',
      key: 'execution_mode',
      render: (mode: string) => {
        const modeNames: Record<string, string> = {
          sequential: '顺序执行',
          parallel: '并行执行',
          conditional: '条件执行'
        }
        return <Tag>{modeNames[mode] || mode}</Tag>
      }
    },
    {
      title: '分配角色',
      dataIndex: 'assigned_role_id',
      key: 'assigned_role_id',
      render: (roleId: string) => {
        if (!roleId) return <Tag>未分配</Tag>
        const role = roles.find(r => r.id === roleId)
        return role ? <Tag color="blue">{role.name}</Tag> : <Tag>未知</Tag>
      }
    },
    {
      title: '依赖数',
      dataIndex: 'dependencies',
      key: 'dependencies',
      render: (deps: string[]) => <Tag>{deps?.length || 0} 项</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Task) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)} />
          <Popconfirm
            title="确定删除此任务？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  if (!currentOrganizationId) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <h3>请先在「组织概览」中选择或创建一个组织</h3>
        </div>
      </Card>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>任务管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingTask(null)
            form.resetFields()
            setIsModalOpen(true)
          }}
        >
          创建任务
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={loading.tasks}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingTask ? '编辑任务' : '创建任务'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingTask(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          onFinish={editingTask ? handleUpdate : handleCreate}
          layout="vertical"
        >
          <Form.Item name="name" label="任务名称" rules={[{ required: true }]}>
            <Input placeholder="请输入任务名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea placeholder="请输入任务描述" rows={2} />
          </Form.Item>
          <Form.Item name="prompt" label="Prompt">
            <TextArea placeholder="请输入任务执行的 prompt" rows={4} />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select>
              <Select.Option value="high">高</Select.Option>
              <Select.Option value="medium">中</Select.Option>
              <Select.Option value="low">低</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="execution_mode" label="执行模式" initialValue="sequential">
            <Select>
              <Select.Option value="sequential">顺序执行</Select.Option>
              <Select.Option value="parallel">并行执行</Select.Option>
              <Select.Option value="conditional">条件执行</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="assigned_role_id" label="分配角色">
            <Select allowClear placeholder="请选择执行角色">
              {roles.map(r => (
                <Select.Option key={r.id} value={r.id}>{r.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="dependencies" label="依赖任务" initialValue={[]}>
            <Select mode="multiple" allowClear placeholder="选择前置任务">
              {tasks.filter(t => t.id !== editingTask?.id).map(t => (
                <Select.Option key={t.id} value={t.id}>{t.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
