import { Card, Table, Button, Space, Tag, Modal, Form, Input, message, Popconfirm } from 'antd'
import { PlusOutlined, DeleteOutlined, NodeIndexOutlined } from '@ant-design/icons'
import { useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useStore } from '../stores'
import type { DataFlow, DataFlowNode, DataFlowEdge } from '../types'

const nodeColors: Record<string, string> = {
  role: '#1890ff',
  task: '#fa8c16',
  knowledge: '#52c41a',
  input: '#722ed1',
  output: '#eb2f96'
}

export default function DataFlowEditor() {
  const {
    currentOrganizationId,
    dataflows,
    loadDataflows,
    createDataflow,
    updateDataflow,
    deleteDataflow,
    loading
  } = useStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDesignerOpen, setIsDesignerOpen] = useState(false)
  const [editingDataflow, setEditingDataflow] = useState<DataFlow | null>(null)
  const [form] = Form.useForm()
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  useEffect(() => {
    if (currentOrganizationId) {
      loadDataflows(currentOrganizationId)
    }
  }, [currentOrganizationId, loadDataflows])

  const handleCreate = async (values: Partial<DataFlow>) => {
    if (!currentOrganizationId) {
      message.warning('请先选择一个组织')
      return
    }
    try {
      await createDataflow(currentOrganizationId, {
        ...values,
        nodes: [],
        edges: []
      })
      message.success('数据流创建成功')
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      message.error('创建失败')
    }
  }

  const handleDelete = async (dataflowId: string) => {
    if (!currentOrganizationId) return
    try {
      await deleteDataflow(currentOrganizationId, dataflowId)
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  const openDesigner = (dataflow: DataFlow) => {
    setEditingDataflow(dataflow)
    const flowNodes: Node[] = dataflow.nodes.map((node: DataFlowNode) => ({
      id: node.id,
      position: node.position,
      data: { label: node.label || node.type },
      style: {
        background: nodeColors[node.type] || '#fff',
        color: 'white',
        border: `2px solid ${nodeColors[node.type] || '#1890ff'}`,
        borderRadius: 8,
        padding: '10px 20px',
        fontWeight: 500
      }
    }))

    const flowEdges: Edge[] = dataflow.edges.map((edge: DataFlowEdge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.condition,
      animated: true,
      data: { data_mapping: edge.data_mapping }
    }))

    setNodes(flowNodes)
    setEdges(flowEdges)
    setIsDesignerOpen(true)
  }

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge(params, eds))
  }, [setEdges])

  const handleSaveDesigner = async () => {
    if (!currentOrganizationId || !editingDataflow) return

    const updatedDataflow: Partial<DataFlow> = {
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.data?.type || 'role' as const,
        position: node.position,
        label: node.data?.label as string
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        condition: edge.label as string | undefined,
        data_mapping: (edge.data as { data_mapping?: Record<string, unknown> })?.data_mapping || {}
      }))
    }

    try {
      await updateDataflow(currentOrganizationId, editingDataflow.id, updatedDataflow)
      message.success('数据流保存成功')
      setIsDesignerOpen(false)
    } catch {
      message.error('保存失败')
    }
  }

  const addNode = (type: string) => {
    const newNode: Node = {
      id: `${type}-${Date.now()}`,
      position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: { label: `新${type}` },
      style: {
        background: nodeColors[type] || '#fff',
        color: 'white',
        border: `2px solid ${nodeColors[type] || '#1890ff'}`,
        borderRadius: 8,
        padding: '10px 20px'
      }
    }
    setNodes((nds) => [...nds, newNode])
  }

  const columns = [
    {
      title: '数据流名称',
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
      title: '节点数',
      dataIndex: 'nodes',
      key: 'nodes',
      render: (nodes: DataFlowNode[]) => <Tag>{nodes?.length || 0}</Tag>
    },
    {
      title: '连接数',
      dataIndex: 'edges',
      key: 'edges',
      render: (edges: DataFlowEdge[]) => <Tag>{edges?.length || 0}</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: DataFlow) => (
        <Space>
          <Button size="small" icon={<NodeIndexOutlined />} onClick={() => openDesigner(record)}>
            设计
          </Button>
          <Popconfirm
            title="确定删除此数据流？"
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
        <h2 style={{ margin: 0 }}>数据流设计</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingDataflow(null)
            form.resetFields()
            setIsModalOpen(true)
          }}
        >
          创建数据流
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={dataflows}
        rowKey="id"
        loading={loading.dataflows}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="创建数据流"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          onFinish={handleCreate}
          layout="vertical"
        >
          <Form.Item name="name" label="数据流名称" rules={[{ required: true }]}>
            <Input placeholder="请输入数据流名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述" rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="数据流设计器"
        open={isDesignerOpen}
        onCancel={() => setIsDesignerOpen(false)}
        onOk={handleSaveDesigner}
        width={1000}
        height={700}
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button onClick={() => addNode('role')}>+ 角色节点</Button>
            <Button onClick={() => addNode('task')}>+ 任务节点</Button>
            <Button onClick={() => addNode('knowledge')}>+ 知识节点</Button>
            <Button onClick={() => addNode('input')}>+ 输入节点</Button>
            <Button onClick={() => addNode('output')}>+ 输出节点</Button>
          </Space>
          <span style={{ marginLeft: 16, fontSize: 12, color: '#666' }}>
            拖拽节点进行连接来创建数据流
          </span>
        </div>
        <div style={{ height: 500 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
          >
            <Background />
          </ReactFlow>
        </div>
      </Modal>
    </div>
  )
}
