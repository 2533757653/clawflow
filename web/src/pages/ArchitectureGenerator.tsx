import { Card, Button, Space, Tag, Modal, Form, Input, Row, Col, Typography, Alert, Divider, message } from 'antd'
import { RobotOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useStore } from '../stores'
import { generatorApi } from '../services/api'
import type { GenerateResponse, GeneratedRole, GeneratedSystem } from '../types'

const { Text } = Typography

interface ArchitectureGeneratorProps {
  open: boolean
  onClose: () => void
}

export default function ArchitectureGenerator({ open, onClose }: ArchitectureGeneratorProps) {
  const {
    currentOrganizationId,
    createRole,
    createSystem,
    loadRoles,
    loadSystems
  } = useStore()

  const [description, setDescription] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [applying, setApplying] = useState(false)
  const [applied, setApplied] = useState(false)

  const handleGenerate = async () => {
    if (!description.trim()) {
      message.warning('请输入组织描述')
      return
    }

    setGenerating(true)
    try {
      const res = await generatorApi.generate({ description })
      setResult(res)
      if (res.suggestions.length > 0 && res.roles.length === 0) {
        message.warning(res.suggestions[0])
      }
    } catch (err) {
      message.error('生成失败')
      console.error(err)
    } finally {
      setGenerating(false)
    }
  }

  const handleApply = async () => {
    if (!currentOrganizationId || !result) {
      message.warning('请先选择一个组织')
      return
    }

    setApplying(true)
    try {
      for (const role of result.roles) {
        await createRole(currentOrganizationId, {
          name: role.name,
          description: role.description,
          responsibilities: role.responsibilities,
          hierarchy_level: role.hierarchy_level,
          permission_level: 'member'
        })
      }

      await loadRoles(currentOrganizationId)
      await loadAvailableExecutorsForOrg(currentOrganizationId)

      for (const sys of result.systems) {
        await createSystem(currentOrganizationId, {
          name: sys.name,
          description: sys.description,
          actors: [],
          nodes: [],
          edges: [],
          state: 'initialized',
          loop_count: 0,
          max_depth: 3
        })
      }

      await loadSystems(currentOrganizationId)
      setApplied(true)
      message.success('架构已应用到组织')
    } catch (err) {
      message.error('应用失败')
      console.error(err)
    } finally {
      setApplying(false)
    }
  }

  const loadAvailableExecutorsForOrg = async (orgId: string) => {
    const { loadAvailableExecutors } = useStore.getState()
    await loadAvailableExecutors(orgId)
  }

  const renderRoleCard = (role: GeneratedRole, type: 'decider' | 'actor' | 'feedbacker') => {
    const colors = {
      decider: { bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', icon: '🎯' },
      actor: { bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', icon: '⚡' },
      feedbacker: { bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', icon: '🔍' }
    }
    const c = colors[type]

    return (
      <Card
        size="small"
        style={{
          background: c.bg,
          color: 'white',
          marginBottom: 8
        }}
        bodyStyle={{ padding: 12 }}
      >
        <Space>
          <span style={{ fontSize: 18 }}>{c.icon}</span>
          <div>
            <div style={{ fontWeight: 'bold' }}>{role.name}</div>
            <div style={{ fontSize: 11, opacity: 0.9 }}>{role.description}</div>
            {role.responsibilities.length > 0 && (
              <div style={{ fontSize: 10, marginTop: 4 }}>
                职责: {role.responsibilities.slice(0, 3).join(', ')}
              </div>
            )}
          </div>
        </Space>
      </Card>
    )
  }

  const renderSystemPreview = (sys: GeneratedSystem, isMain: boolean = false) => {
    return (
      <Card
        size="small"
        title={isMain ? `主系统: ${sys.name}` : `子系统: ${sys.name}`}
        extra={<Tag>{sys.template_type}</Tag>}
        style={{ marginBottom: 16 }}
      >
        <Row gutter={16}>
          <Col span={8}>
            {renderRoleCard(sys.decider, 'decider')}
          </Col>
          <Col span={8}>
            <div style={{ padding: '8px 0' }}>
              <Text strong>行动者</Text>
              {sys.actors.map((actor, idx) => (
                actor.is_nested_system ? (
                  <Tag key={idx} color="purple" style={{ marginLeft: 4 }}>
                    🔄 {actor.name}
                  </Tag>
                ) : (
                  <Tag key={idx} style={{ marginLeft: 4, background: '#fff7e6', borderColor: '#fa8c16' }}>
                    ⚡ {actor.name}
                  </Tag>
                )
              ))}
            </div>
          </Col>
          <Col span={8}>
            {renderRoleCard(sys.feedbacker, 'feedbacker')}
          </Col>
        </Row>
      </Card>
    )
  }

  return (
    <Modal
      title={
        <Space>
          <RobotOutlined />
          <span>架构生成器</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      width={800}
      footer={null}
    >
      <Form layout="vertical">
        <Form.Item label="组织描述">
          <Input.TextArea
            placeholder='描述你的组织，例如：产品经理（负责决策方向）、设计师（负责UI设计）、开发人员（负责编码实现）、测试人员（负责质量把关）'
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Form.Item>
        <Form.Item label="提示">
          <Text type="secondary">
            使用逗号分隔不同角色，角色名后的括号内可添加描述。
            关键词如"负责"、"监督"、"执行"可帮助系统识别角色类型。
          </Text>
        </Form.Item>
        <Button
          type="primary"
          icon={<RobotOutlined />}
          onClick={handleGenerate}
          loading={generating}
          block
          style={{ marginBottom: 16 }}
        >
          生成架构
        </Button>
      </Form>

      {result && (
        <>
          {result.suggestions.length > 0 && (
            <Alert
              message="生成提示"
              description={result.suggestions.join(' ')}
              type={result.roles.length > 0 ? 'info' : 'warning'}
              style={{ marginBottom: 16 }}
            />
          )}

          {result.roles.length > 0 && (
            <>
              <Divider orientation="left">识别的角色 ({result.roles.length})</Divider>
              <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
                {result.roles.map((role, idx) => (
                  <Col span={8} key={idx}>
                    <Card size="small">
                      <Space>
                        <Tag color={
                          role.role_type === 'decider' ? 'purple' :
                          role.role_type === 'feedbacker' ? 'cyan' : 'orange'
                        }>
                          {role.role_type === 'decider' ? '🎯' : role.role_type === 'feedbacker' ? '🔍' : '⚡'}
                        </Tag>
                        <Text strong>{role.name}</Text>
                      </Space>
                      {role.description && (
                        <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                          {role.description}
                        </div>
                      )}
                    </Card>
                  </Col>
                ))}
              </Row>
            </>
          )}

          {result.systems.length > 0 && (
            <>
              <Divider orientation="left">生成的系统架构</Divider>
              {result.systems.map((sys, idx) => renderSystemPreview(sys, idx === 0))}
            </>
          )}

          {result.roles.length > 0 && currentOrganizationId && (
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={handleApply}
              loading={applying}
              disabled={applied}
              block
            >
              {applied ? '已应用 ✓' : '应用到当前组织'}
            </Button>
          )}
        </>
      )}
    </Modal>
  )
}