import { Card, Form, Input, Button, Space, message, Select, Modal, Table, Tag, Popconfirm } from 'antd'
import { SaveOutlined, RocketOutlined, PlusOutlined, DeleteOutlined, TeamOutlined } from '@ant-design/icons'
import { useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  ReactFlowProvider
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useStore } from '../stores'
import type { ComponentType, Organization, Role } from '../types'

const { TextArea } = Input

const componentColors: Record<ComponentType, string> = {
  header: '#1890ff',
  role_list: '#52c41a',
  task_list: '#fa8c16',
  knowledge: '#722ed1',
  data_flow: '#eb2f96',
  skill: '#13c2c2',
  prompt: '#faad14',
  memory: '#f5222d',
  custom: '#000000'
}

const componentLabels: Record<ComponentType, string> = {
  header: '组织标题',
  role_list: '角色列表',
  task_list: '任务列表',
  knowledge: '知识库',
  data_flow: '数据流',
  skill: '技能中心',
  prompt: '初始 Prompt',
  memory: '上下文记忆',
  custom: '自定义组件'
}

export default function OrganizationEditor() {
  const {
    currentOrganizationId,
    organizations,
    roles,
    updateOrganization,
    deployOrganization
  } = useStore()

  const [form] = Form.useForm()
  const [isDesignerOpen, setIsDesignerOpen] = useState(false)
  const [isRoleSelectOpen, setIsRoleSelectOpen] = useState(false)
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([])
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const currentOrg = organizations.find(o => o.id === currentOrganizationId)

  const orgRoles = roles.filter(r => currentOrg?.role_ids?.includes(r.id))
  const availableRoles = roles.filter(r => !currentOrg?.role_ids?.includes(r.id))

  useEffect(() => {
    if (currentOrg) {
      form.setFieldsValue({
        name: currentOrg.name,
        description: currentOrg.description,
        logo: currentOrg.logo,
        initial_prompt: currentOrg.initial_prompt,
        input_role_id: currentOrg.input_role_id
      })
    }
  }, [currentOrg, form])

  const handleSave = async (values: Partial<Organization>) => {
    if (!currentOrganizationId) {
      message.warning('请先选择一个组织')
      return
    }
    try {
      await updateOrganization(currentOrganizationId, values)
      message.success('保存成功')
    } catch {
      message.error('保存失败')
    }
  }

  const handleDeploy = async () => {
    if (!currentOrganizationId) {
      message.warning('请先选择一个组织')
      return
    }
    try {
      await deployOrganization(currentOrganizationId)
      message.success('部署成功，Agent 组织已创建到 OpenClaw 工作区')
    } catch {
      message.error('部署失败')
    }
  }

  const handleAddRoles = async () => {
    if (!currentOrganizationId || selectedRoleIds.length === 0) return
    try {
      const newRoleIds = [...(currentOrg?.role_ids || []), ...selectedRoleIds]
      await updateOrganization(currentOrganizationId, { role_ids: newRoleIds })
      message.success(`已添加 ${selectedRoleIds.length} 个角色`)
      setIsRoleSelectOpen(false)
      setSelectedRoleIds([])
    } catch {
      message.error('添加角色失败')
    }
  }

  const handleRemoveRole = async (roleId: string) => {
    if (!currentOrganizationId) return
    try {
      const newRoleIds = (currentOrg?.role_ids || []).filter(id => id !== roleId)
      await updateOrganization(currentOrganizationId, { role_ids: newRoleIds })
      message.success('角色已移除')
    } catch {
      message.error('移除角色失败')
    }
  }

  const openDesigner = () => {
    if (!currentOrg) return

    const flowNodes = currentOrg.layout.map((comp, index) => ({
      id: comp.id,
      position: { x: comp.position?.x || (index % 3) * 250, y: comp.position?.y || Math.floor(index / 3) * 150 },
      data: {
        label: comp.label || componentLabels[comp.type],
        componentType: comp.type,
        config: comp.config || {}
      },
      style: {
        background: componentColors[comp.type] || '#fff',
        color: 'white',
        border: `2px solid ${componentColors[comp.type] || '#1890ff'}`,
        borderRadius: 8,
        padding: '10px 20px',
        width: Number(comp.size?.width) || 200,
        height: Number(comp.size?.height) || 80
      }
    }))

    setNodes(flowNodes)
    setEdges([])
    setIsDesignerOpen(true)
  }

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge(params, eds))
  }, [setEdges])

  const addNode = (type: ComponentType) => {
    const newNode = {
      id: `component-${Date.now()}`,
      position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: {
        label: componentLabels[type],
        componentType: type,
        config: {}
      },
      style: {
        background: componentColors[type] || '#fff',
        color: 'white',
        border: `2px solid ${componentColors[type] || '#1890ff'}`,
        borderRadius: 8,
        padding: '10px 20px',
        width: 200,
        height: 80
      }
    }
    setNodes((nds) => [...nds, newNode])
  }

  const handleSaveDesigner = async () => {
    if (!currentOrganizationId || !currentOrg) return

    const layout = nodes.map(node => ({
      id: node.id,
      type: node.data.componentType,
      position: { x: node.position.x, y: node.position.y },
      size: { width: Number(node.style?.width) || 200, height: Number(node.style?.height) || 80 },
      config: node.data.config,
      label: node.data.label
    }))

    try {
      await updateOrganization(currentOrganizationId, { layout } as Partial<Organization>)
      message.success('布局保存成功')
      setIsDesignerOpen(false)
    } catch {
      message.error('保存失败')
    }
  }

  if (!currentOrganizationId || !currentOrg) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <h3>请先在「组织概览」中选择一个组织</h3>
        </div>
      </Card>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>组织设置</h2>
        <p style={{ color: '#666', marginTop: 8 }}>
          当前组织：<strong>{currentOrg.name}</strong>
        </p>
      </div>

      <Card
        title="基本信息"
        extra={
          <Space>
            <Button icon={<SaveOutlined />} onClick={() => form.submit()}>
              保存更改
            </Button>
            <Button
              type="primary"
              icon={<RocketOutlined />}
              onClick={handleDeploy}
              disabled={currentOrg.status === 'deployed'}
            >
              部署到 OpenClaw
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          onFinish={handleSave}
          layout="vertical"
          initialValues={{
            name: currentOrg.name,
            description: currentOrg.description,
            logo: currentOrg.logo,
            initial_prompt: currentOrg.initial_prompt,
            input_role_id: currentOrg.input_role_id
          }}
        >
          <Form.Item name="name" label="组织名称" rules={[{ required: true }]}>
            <Input placeholder="请输入组织名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea placeholder="请输入组织描述" rows={3} />
          </Form.Item>
          <Form.Item name="logo" label="Logo URL">
            <Input placeholder="请输入 Logo URL" />
          </Form.Item>
          <Form.Item name="initial_prompt" label="初始 Prompt">
            <TextArea placeholder="组织启动时发送给输入角色的初始 prompt" rows={4} />
          </Form.Item>
          <Form.Item name="input_role_id" label="输入角色">
            <Select allowClear placeholder="选择接收外部输入的角色">
              {roles.map(role => (
                <Select.Option key={role.id} value={role.id}>{role.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Card>

      <Card title="可视化布局" style={{ marginTop: 24 }}>
        <p style={{ color: '#666', marginBottom: 16 }}>
          通过拖拽组件构建组织的可视化概览。点击「编辑布局」开始设计。
        </p>
        <Button type="primary" onClick={openDesigner}>
          编辑布局
        </Button>

        {currentOrg.layout && currentOrg.layout.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <h4>已添加的组件：</h4>
            <Space wrap>
              {currentOrg.layout.map(comp => (
                <div
                  key={comp.id}
                  style={{
                    padding: '8px 16px',
                    background: componentColors[comp.type],
                    color: 'white',
                    borderRadius: 4
                  }}
                >
                  {componentLabels[comp.type]}
                </div>
              ))}
            </Space>
          </div>
        )}
      </Card>

      <Card title="部署状态" style={{ marginTop: 24 }}>
        <div style={{ display: 'flex', gap: 24 }}>
          <div>
            <p style={{ margin: 0, color: '#666' }}>当前状态</p>
            <p style={{ margin: '8px 0 0 0', fontSize: 18 }}>
              {currentOrg.status.toUpperCase()}
            </p>
          </div>
          <div>
            <p style={{ margin: 0, color: '#666' }}>创建时间</p>
            <p style={{ margin: '8px 0 0 0' }}>
              {new Date(currentOrg.created_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p style={{ margin: 0, color: '#666' }}>最后更新</p>
            <p style={{ margin: '8px 0 0 0' }}>
              {new Date(currentOrg.updated_at).toLocaleString()}
            </p>
          </div>
        </div>
      </Card>

      <Card title="组织角色" style={{ marginTop: 24 }}>
        <p style={{ color: '#666', marginBottom: 16 }}>
          管理此组织包含的角色。角色是全局资源，可以被多个组织引用。
        </p>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setSelectedRoleIds([])
            setIsRoleSelectOpen(true)
          }}
          disabled={availableRoles.length === 0}
        >
          添加角色
        </Button>

        {orgRoles.length > 0 ? (
          <Table
            dataSource={orgRoles}
            rowKey="id"
            pagination={false}
            style={{ marginTop: 16 }}
            columns={[
              {
                title: '角色名称',
                dataIndex: 'name',
                key: 'name',
                render: (name: string, record: Role) => (
                  <Space>
                    <TeamOutlined />
                    {name}
                    {record.source === 'agency-agents' && (
                      <Tag color="purple" style={{ fontSize: 10 }}>Agency</Tag>
                    )}
                  </Space>
                )
              },
              {
                title: '部门',
                dataIndex: 'division',
                key: 'division',
                render: (div: string) => div ? <Tag>{div}</Tag> : '-'
              },
              {
                title: '层级',
                dataIndex: 'hierarchy_level',
                key: 'hierarchy_level',
                render: (level: number) => <Tag color="blue">Level {level}</Tag>
              },
              {
                title: '操作',
                key: 'action',
                render: (_: unknown, record: Role) => (
                  <Popconfirm
                    title="确定从此组织移除此角色？"
                    onConfirm={() => handleRemoveRole(record.id)}
                  >
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                )
              }
            ]}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: 24, color: '#999' }}>
            此组织尚未关联任何角色
          </div>
        )}
      </Card>

      <Modal
        title="组织布局设计器"
        open={isDesignerOpen}
        onCancel={() => setIsDesignerOpen(false)}
        onOk={handleSaveDesigner}
        width={1200}
      >
        <div style={{ marginBottom: 16 }}>
          <Space wrap>
            <span style={{ fontWeight: 500 }}>添加组件：</span>
            <Button size="small" onClick={() => addNode('header')}>组织标题</Button>
            <Button size="small" onClick={() => addNode('role_list')}>角色列表</Button>
            <Button size="small" onClick={() => addNode('task_list')}>任务列表</Button>
            <Button size="small" onClick={() => addNode('knowledge')}>知识库</Button>
            <Button size="small" onClick={() => addNode('data_flow')}>数据流</Button>
            <Button size="small" onClick={() => addNode('skill')}>技能中心</Button>
            <Button size="small" onClick={() => addNode('prompt')}>初始 Prompt</Button>
            <Button size="small" onClick={() => addNode('memory')}>上下文记忆</Button>
          </Space>
          <p style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            点击节点右上角的删除按钮可移除组件。拖拽节点进行连接。
          </p>
        </div>
        <div style={{ height: 500 }}>
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
            >
              <Background />
            </ReactFlow>
          </ReactFlowProvider>
        </div>
      </Modal>

      <Modal
        title="添加角色到此组织"
        open={isRoleSelectOpen}
        onCancel={() => {
          setIsRoleSelectOpen(false)
          setSelectedRoleIds([])
        }}
        onOk={handleAddRoles}
        okText={`添加 ${selectedRoleIds.length} 个角色`}
        okButtonProps={{ disabled: selectedRoleIds.length === 0 }}
      >
        <p style={{ marginBottom: 16 }}>选择要添加到此组织的角色（可多选）：</p>
        <div style={{ maxHeight: 400, overflow: 'auto' }}>
          {availableRoles.length > 0 ? (
            availableRoles.map(role => (
              <div
                key={role.id}
                style={{
                  padding: '8px 12px',
                  marginBottom: 8,
                  border: '1px solid #d9d9d9',
                  borderRadius: 4,
                  cursor: 'pointer',
                  background: selectedRoleIds.includes(role.id) ? '#e6f7ff' : '#fff'
                }}
                onClick={() => {
                  if (selectedRoleIds.includes(role.id)) {
                    setSelectedRoleIds(selectedRoleIds.filter(id => id !== role.id))
                  } else {
                    setSelectedRoleIds([...selectedRoleIds, role.id])
                  }
                }}
              >
                <Space>
                  <TeamOutlined />
                  <strong>{role.name}</strong>
                  {role.division && <Tag>{role.division}</Tag>}
                  <Tag color="blue">Level {role.hierarchy_level}</Tag>
                  {role.source === 'agency-agents' && (
                    <Tag color="purple" style={{ fontSize: 10 }}>Agency</Tag>
                  )}
                </Space>
                {role.description && (
                  <p style={{ margin: '4px 0 0 24px', color: '#666', fontSize: 12 }}>
                    {role.description}
                  </p>
                )}
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: 24, color: '#999' }}>
              没有可添加的角色（所有角色都已被此组织关联）
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}
