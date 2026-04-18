import { Card, Form, Input, Button, Space, message } from 'antd'
import { SaveOutlined, RocketOutlined } from '@ant-design/icons'
import { useEffect } from 'react'
import { useStore } from '../stores'
import type { Organization } from '../types'

const { TextArea } = Input

export default function OrganizationEditor() {
  const {
    currentOrganizationId,
    organizations,
    updateOrganization,
    deployOrganization
  } = useStore()

  const [form] = Form.useForm()

  const currentOrg = organizations.find(o => o.id === currentOrganizationId)

  useEffect(() => {
    if (currentOrg) {
      form.setFieldsValue({
        name: currentOrg.name,
        description: currentOrg.description,
        logo: currentOrg.logo
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
            logo: currentOrg.logo
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
        </Form>
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
    </div>
  )
}
