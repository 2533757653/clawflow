import { Card, Row, Col, Statistic, Button, List, Tag, Space, message, Modal, Form, Input } from 'antd'
import { PlusOutlined, RocketOutlined, TeamOutlined, DeleteOutlined, EditOutlined, PlayCircleOutlined, StopOutlined, CloudUploadOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useStore } from '../stores'
import type { Organization } from '../types'

const { Meta } = Card

export default function Dashboard() {
  const {
    organizations,
    currentOrganizationId,
    setCurrentOrganization,
    createOrganization,
    deleteOrganization,
    deployOrganization,
    startOrganization,
    stopOrganization,
    loading
  } = useStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()

  const handleCreate = async (values: Partial<Organization>) => {
    try {
      const org = await createOrganization(values)
      message.success('组织创建成功')
      setCurrentOrganization(org.id)
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      message.error('创建失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteOrganization(id)
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  const handleDeploy = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await deployOrganization(id)
      message.success('部署成功')
    } catch {
      message.error('部署失败')
    }
  }

  const handleStart = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await startOrganization(id)
      message.success('组织已开启')
    } catch {
      message.error('开启失败')
    }
  }

  const handleStop = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await stopOrganization(id)
      message.success('组织已停止')
    } catch {
      message.error('停止失败')
    }
  }

  const statusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'default',
      deployed: 'blue',
      running: 'green',
      stopped: 'red'
    }
    return colors[status] || 'default'
  }

  const currentOrg = organizations.find(o => o.id === currentOrganizationId)

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <h2 style={{ margin: 0 }}>组织概览</h2>
          {currentOrg && (
            <Tag color="blue">{currentOrg.name}</Tag>
          )}
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          创建组织
        </Button>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="组织总数"
              value={organizations.length}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已部署"
              value={organizations.filter(o => o.status === 'deployed' || o.status === 'running').length}
              prefix={<CloudUploadOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="草稿"
              value={organizations.filter(o => o.status === 'draft').length}
              prefix={<EditOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中"
              value={organizations.filter(o => o.status === 'running').length}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <h3 style={{ marginBottom: 16 }}>组织列表</h3>
      <List
        grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
        dataSource={organizations}
        loading={loading.organizations}
        renderItem={(org) => (
          <List.Item>
            <Card
              hoverable
              style={{ borderColor: currentOrganizationId === org.id ? '#1890ff' : undefined }}
              onClick={() => setCurrentOrganization(org.id)}
              actions={[
                org.status === 'draft' && (
                  <CloudUploadOutlined key="deploy" onClick={(e) => handleDeploy(org.id, e)} />
                ),
                org.status === 'deployed' && (
                  <PlayCircleOutlined key="start" onClick={(e) => handleStart(org.id, e)} />
                ),
                org.status === 'running' && (
                  <StopOutlined key="stop" onClick={(e) => handleStop(org.id, e)} />
                ),
                <DeleteOutlined key="delete" onClick={(e) => {
                  e.stopPropagation()
                  Modal.confirm({
                    title: '确认删除',
                    content: '确定要删除这个组织吗？',
                    onOk: () => handleDelete(org.id)
                  })
                }} />
              ].filter(Boolean)}
            >
              <Meta
                avatar={<RocketOutlined style={{ fontSize: 32, color: '#1890ff' }} />}
                title={org.name}
                description={
                  <Space direction="vertical" size="small">
                    <span>{org.description || '暂无描述'}</span>
                    <Tag color={statusColor(org.status)}>{org.status.toUpperCase()}</Tag>
                  </Space>
                }
              />
            </Card>
          </List.Item>
        )}
      />

      <Modal
        title="创建组织"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          onFinish={handleCreate}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="组织名称"
            rules={[{ required: true, message: '请输入组织名称' }]}
          >
            <Input placeholder="请输入组织名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea placeholder="请输入组织描述" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
