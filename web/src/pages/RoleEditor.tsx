import { Card, Table, Button, Space, Tag, Tree, Modal, Form, Input, Select, message, Popconfirm } from 'antd'
import type { TreeDataNode } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, SwapOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useStore } from '../stores'
import type { Role, RoleHierarchy } from '../types'
import { roleApi } from '../services/api'

const { TextArea } = Input

export default function RoleEditor() {
  const {
    currentOrganizationId,
    roles,
    loadRoles,
    createRole,
    updateRole,
    deleteRole,
    loading
  } = useStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isHierarchyModalOpen, setIsHierarchyModalOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [form] = Form.useForm()
  const [hierarchyData, setHierarchyData] = useState<RoleHierarchy | null>(null)

  useEffect(() => {
    if (currentOrganizationId) {
      loadRoles(currentOrganizationId)
    }
  }, [currentOrganizationId, loadRoles])

  const handleCreate = async (values: Partial<Role>) => {
    if (!currentOrganizationId) {
      message.warning('请先选择一个组织')
      return
    }
    try {
      await createRole(currentOrganizationId, values)
      message.success('角色创建成功')
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      message.error('创建失败')
    }
  }

  const handleUpdate = async (values: Partial<Role>) => {
    if (!currentOrganizationId || !editingRole) return
    try {
      await updateRole(currentOrganizationId, editingRole.id, values)
      message.success('角色更新成功')
      setIsModalOpen(false)
      setEditingRole(null)
      form.resetFields()
    } catch {
      message.error('更新失败')
    }
  }

  const handleDelete = async (roleId: string) => {
    if (!currentOrganizationId) return
    try {
      await deleteRole(currentOrganizationId, roleId)
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  const openEditModal = (role: Role) => {
    setEditingRole(role)
    form.setFieldsValue(role)
    setIsModalOpen(true)
  }

  const showHierarchy = async () => {
    if (!currentOrganizationId || roles.length === 0) return
    try {
      const topRole = roles.find(r => !r.reports_to)
      if (topRole) {
        const hierarchy = await roleApi.getHierarchy(currentOrganizationId, topRole.id)
        setHierarchyData(hierarchy)
        setIsHierarchyModalOpen(true)
      } else {
        message.info('没有找到顶级角色')
      }
    } catch {
      message.error('获取层级失败')
    }
  }

  const renderHierarchyTree = (node: RoleHierarchy): TreeDataNode => ({
    title: (
      <span>
        {node.name}
        <Tag color="blue" style={{ marginLeft: 8 }}>L{node.hierarchy_level}</Tag>
      </span>
    ),
    key: node.id,
    children: node.children?.map(child => renderHierarchyTree(child))
  })

  const columns = [
    {
      title: '角色名称',
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
      title: '层级',
      dataIndex: 'hierarchy_level',
      key: 'hierarchy_level',
      render: (level: number) => <Tag color="blue">Level {level}</Tag>
    },
    {
      title: '权限',
      dataIndex: 'permission_level',
      key: 'permission_level',
      render: (level: string) => {
        const colors: Record<string, string> = {
          admin: 'red',
          manager: 'orange',
          member: 'green',
          readonly: 'default'
        }
        return <Tag color={colors[level]}>{level}</Tag>
      }
    },
    {
      title: '汇报给',
      dataIndex: 'reports_to',
      key: 'reports_to',
      render: (reportsTo: string) => {
        if (!reportsTo) return <Tag>顶级角色</Tag>
        const parent = roles.find(r => r.id === reportsTo)
        return parent ? <Tag>{parent.name}</Tag> : <Tag>未知</Tag>
      }
    },
    {
      title: '职责数',
      dataIndex: 'responsibilities',
      key: 'responsibilities',
      render: (resp: string[]) => <Tag>{resp.length} 项</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Role) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)} />
          <Popconfirm
            title="确定删除此角色？"
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
        <h2 style={{ margin: 0 }}>角色管理</h2>
        <Space>
          <Button icon={<SwapOutlined />} onClick={showHierarchy}>
            查看层级
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => {
            setEditingRole(null)
            form.resetFields()
            setIsModalOpen(true)
          }}>
            创建角色
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={roles}
        rowKey="id"
        loading={loading.roles}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingRole ? '编辑角色' : '创建角色'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingRole(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          onFinish={editingRole ? handleUpdate : handleCreate}
          layout="vertical"
        >
          <Form.Item name="name" label="角色名称" rules={[{ required: true }]}>
            <Input placeholder="请输入角色名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea placeholder="请输入角色描述" rows={2} />
          </Form.Item>
          <Form.Item name="hierarchy_level" label="层级" initialValue={1}>
            <Select>
              <Select.Option value={1}>Level 1 - 基础角色</Select.Option>
              <Select.Option value={2}>Level 2 - 小组负责人</Select.Option>
              <Select.Option value={3}>Level 3 - 部门负责人</Select.Option>
              <Select.Option value={4}>Level 4 - 高层管理</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="permission_level" label="权限级别" initialValue="member">
            <Select>
              <Select.Option value="admin">管理员</Select.Option>
              <Select.Option value="manager">经理</Select.Option>
              <Select.Option value="member">成员</Select.Option>
              <Select.Option value="readonly">只读</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="reports_to" label="汇报对象">
            <Select allowClear placeholder="请选择汇报对象">
              {roles.filter(r => r.id !== editingRole?.id).map(r => (
                <Select.Option key={r.id} value={r.id}>{r.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="responsibilities" label="职责" initialValue={[]}>
            <Select mode="tags" placeholder="输入职责后按回车添加">
            </Select>
          </Form.Item>
          <Form.Item name="required_skills" label="所需技能" initialValue={[]}>
            <Select mode="tags" placeholder="输入技能后按回车添加">
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="角色层级结构"
        open={isHierarchyModalOpen}
        onCancel={() => setIsHierarchyModalOpen(false)}
        footer={null}
        width={400}
      >
        {hierarchyData && (
          <Tree
            treeData={[renderHierarchyTree(hierarchyData)]}
            defaultExpandAll
          />
        )}
      </Modal>
    </div>
  )
}
