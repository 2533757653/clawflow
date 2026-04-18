import { Card, Table, Button, Space, Tag, Modal, Form, Input, Select, message, Popconfirm, Row, Col, Steps, Collapse, Badge, Typography } from 'antd'
import { PlusOutlined, DeleteOutlined, PlayCircleOutlined, StopOutlined, FastForwardOutlined, RobotOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useStore } from '../stores'
import type { AgentSystem, ExecutorUnit, ExecutorType } from '../types'
import ArchitectureGenerator from './ArchitectureGenerator'

const { Panel } = Collapse
const { Text } = Typography

export default function SystemEditor() {
  const {
    currentOrganizationId,
    systems,
    availableExecutors,
    systemSteps,
    loading,
    loadSystems,
    createSystem,
    deleteSystem,
    setSystemDecider,
    addSystemActor,
    removeSystemActor,
    setSystemFeedbacker,
    startSystem,
    stopSystem,
    executeSystemLoop,
    loadSystemSteps,
    loadAvailableExecutors
  } = useStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isGeneratorOpen, setIsGeneratorOpen] = useState(false)
  const [selectedSystem, setSelectedSystem] = useState<AgentSystem | null>(null)
  const [deciderType, setDeciderType] = useState<ExecutorType>('role')
  const [actorType, setActorType] = useState<ExecutorType>('role')
  const [feedbackerType, setFeedbackerType] = useState<ExecutorType>('role')
  const [form] = Form.useForm()

  useEffect(() => {
    if (currentOrganizationId) {
      loadSystems(currentOrganizationId)
      loadAvailableExecutors(currentOrganizationId)
    }
  }, [currentOrganizationId, loadSystems, loadAvailableExecutors])

  const handleCreate = async (values: Partial<AgentSystem>) => {
    if (!currentOrganizationId) {
      message.warning('请先选择一个组织')
      return
    }
    try {
      const system = await createSystem(currentOrganizationId, {
        ...values,
        actors: [],
        nodes: [],
        edges: [],
        state: 'initialized',
        loop_count: 0,
        max_depth: 3
      })
      setSelectedSystem(system)
      message.success('系统创建成功')
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      message.error('创建失败')
    }
  }

  const handleDelete = async (systemId: string) => {
    if (!currentOrganizationId) return
    try {
      await deleteSystem(currentOrganizationId, systemId)
      if (selectedSystem?.id === systemId) {
        setSelectedSystem(null)
      }
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  const handleSetDecider = async (type: ExecutorType, id: string) => {
    if (!currentOrganizationId || !selectedSystem) return
    const executor: ExecutorUnit = {
      type,
      role_id: type === 'role' ? id : undefined,
      system_id: type === 'system' ? id : undefined,
      depth: 0
    }
    try {
      await setSystemDecider(currentOrganizationId, selectedSystem.id, executor)
      message.success('决策者已设置')
    } catch {
      message.error('设置失败')
    }
  }

  const handleAddActor = async (type: ExecutorType, id: string) => {
    if (!currentOrganizationId || !selectedSystem) return
    const executor: ExecutorUnit = {
      type,
      role_id: type === 'role' ? id : undefined,
      system_id: type === 'system' ? id : undefined,
      depth: 0
    }
    try {
      await addSystemActor(currentOrganizationId, selectedSystem.id, executor)
      message.success('行动者已添加')
    } catch {
      message.error('添加失败')
    }
  }

  const handleRemoveActor = async (actorIdx: number) => {
    if (!currentOrganizationId || !selectedSystem) return
    try {
      await removeSystemActor(currentOrganizationId, selectedSystem.id, actorIdx)
      message.success('行动者已移除')
    } catch {
      message.error('移除失败')
    }
  }

  const handleSetFeedbacker = async (type: ExecutorType, id: string) => {
    if (!currentOrganizationId || !selectedSystem) return
    const executor: ExecutorUnit = {
      type,
      role_id: type === 'role' ? id : undefined,
      system_id: type === 'system' ? id : undefined,
      depth: 0
    }
    try {
      await setSystemFeedbacker(currentOrganizationId, selectedSystem.id, executor)
      message.success('反馈者已设置')
    } catch {
      message.error('设置失败')
    }
  }

  const handleStart = async () => {
    if (!currentOrganizationId || !selectedSystem) return
    try {
      await startSystem(currentOrganizationId, selectedSystem.id)
      message.success('系统已启动')
    } catch {
      message.error('启动失败')
    }
  }

  const handleStop = async () => {
    if (!currentOrganizationId || !selectedSystem) return
    try {
      await stopSystem(currentOrganizationId, selectedSystem.id)
      message.success('系统已停止')
    } catch {
      message.error('停止失败')
    }
  }

  const handleExecuteLoop = async () => {
    if (!currentOrganizationId || !selectedSystem) return
    try {
      await executeSystemLoop(currentOrganizationId, selectedSystem.id)
      message.info('执行了一步')
    } catch {
      message.error('执行失败')
    }
  }

  const handleSelectSystem = async (system: AgentSystem) => {
    setSelectedSystem(system)
    if (currentOrganizationId) {
      await loadSystemSteps(currentOrganizationId, system.id)
    }
  }

  const getExecutorDisplayName = (executor?: ExecutorUnit) => {
    if (!executor) return '未设置'
    if (executor.name) return executor.name
    if (executor.type === 'role') return executor.role_id || '未知角色'
    if (executor.type === 'system') return executor.system_id || '未知系统'
    return '未知'
  }

  const canStartSystem = selectedSystem?.decider && selectedSystem.actors.length > 0 && selectedSystem.feedbacker

  const roleExecutors = availableExecutors.roles.map(r => ({ label: r.name, value: r.id }))
  const systemExecutors = availableExecutors.systems.map(s => ({ label: `${s.name} (系统)`, value: s.id }))

  const columns = [
    {
      title: '系统名称',
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
      title: '状态',
      dataIndex: 'state',
      key: 'state',
      render: (state: string) => {
        const colors: Record<string, string> = {
          initialized: 'default',
          running: 'green',
          stopped: 'orange',
          terminated: 'red'
        }
        return <Tag color={colors[state] || 'default'}>{state}</Tag>
      }
    },
    {
      title: '循环',
      dataIndex: 'loop_count',
      key: 'loop_count',
      render: (count: number) => <Tag>{count}</Tag>
    },
    {
      title: '决策者',
      dataIndex: 'decider',
      key: 'decider',
      render: (decider?: ExecutorUnit) => {
        if (!decider) return <Tag>未设置</Tag>
        return (
          <Tag color={decider.type === 'system' ? 'purple' : 'blue'}>
            {decider.type === 'system' ? '🔄' : '👤'} {getExecutorDisplayName(decider)}
          </Tag>
        )
      }
    },
    {
      title: '行动者数',
      dataIndex: 'actors',
      key: 'actors',
      render: (actors: ExecutorUnit[]) => {
        const systemCount = actors.filter(a => a.type === 'system').length
        const roleCount = actors.filter(a => a.type === 'role').length
        return (
          <Space>
            {roleCount > 0 && <Tag>👤 {roleCount}</Tag>}
            {systemCount > 0 && <Tag color="purple">🔄 {systemCount}</Tag>}
          </Space>
        )
      }
    },
    {
      title: '反馈者',
      dataIndex: 'feedbacker',
      key: 'feedbacker',
      render: (feedbacker?: ExecutorUnit) => {
        if (!feedbacker) return <Tag>未设置</Tag>
        return (
          <Tag color={feedbacker.type === 'system' ? 'purple' : 'cyan'}>
            {feedbacker.type === 'system' ? '🔄' : '👤'} {getExecutorDisplayName(feedbacker)}
          </Tag>
        )
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: AgentSystem) => (
        <Space>
          <Button size="small" onClick={() => handleSelectSystem(record)}>查看</Button>
          <Popconfirm
            title="确定删除此系统？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  const renderStepDetails = (step: typeof systemSteps[0]) => {
    const details: string[] = []
    if (step.decider_output) {
      const decider = step.decider_output as Record<string, unknown>
      if (decider.phases) {
        const phases = decider.phases as Record<string, unknown>
        if (phases.decider) {
          const d = phases.decider as Record<string, string>
          details.push(`决策: ${d.directive || JSON.stringify(d)}`)
        }
      }
    }
    if (step.actor_output) {
      const actor = step.actor_output as Record<string, unknown>
      if (actor.actors) {
        const actors = actor.actors as Array<Record<string, unknown>>
        actors.forEach((a, i) => {
          if (a.phases) {
            const phases = a.phases as Record<string, Record<string, string>>
            if (phases.actor?.effect) {
              details.push(`行动者${i + 1}: ${phases.actor.effect}`)
            }
          }
        })
      }
    }
    if (step.feedbacker_output) {
      const feedbacker = step.feedbacker_output as Record<string, unknown>
      if (feedbacker.phases) {
        const phases = feedbacker.phases as Record<string, Record<string, string>>
        if (phases.feedbacker?.observation) {
          details.push(`反馈: ${phases.feedbacker.observation}`)
        }
      }
    }
    return details
  }

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
        <h2 style={{ margin: 0 }}>决策-行动-反馈系统</h2>
        <Space>
          <Badge count={`深度 ${selectedSystem?.max_depth || 3}`} style={{ backgroundColor: '#722ed1' }} />
          <Button
            icon={<RobotOutlined />}
            onClick={() => setIsGeneratorOpen(true)}
          >
            AI 生成架构
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsModalOpen(true)}
          >
            创建系统
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={systems}
        rowKey="id"
        loading={loading.systems}
        pagination={{ pageSize: 10 }}
        expandable={{
          expandedRowRender: (record) => (
            <div style={{ padding: '8px 0' }}>
              <Space wrap>
                <Tag>决策者: {getExecutorDisplayName(record.decider)}</Tag>
                <Tag>行动者: {record.actors.map(a => getExecutorDisplayName(a)).join(', ') || '未设置'}</Tag>
                <Tag>反馈者: {getExecutorDisplayName(record.feedbacker)}</Tag>
              </Space>
            </div>
          )
        }}
      />

      <Modal
        title="创建系统"
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
          <Form.Item name="name" label="系统名称" rules={[{ required: true }]}>
            <Input placeholder="如：产品开发系统" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="描述这个系统的用途" rows={2} />
          </Form.Item>
          <Form.Item name="max_loops" label="最大循环次数">
            <Input type="number" placeholder="留空表示无限制" />
          </Form.Item>
        </Form>
      </Modal>

      {selectedSystem && (
        <Card title={`系统详情: ${selectedSystem.name}`} style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Card size="small" title="🎯 决策者" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                <div style={{ textAlign: 'center', color: 'white' }}>
                  <div style={{ fontSize: 24, marginBottom: 8 }}>
                    {selectedSystem.decider?.type === 'system' ? '🔄' : '👤'}
                  </div>
                  <div style={{ fontWeight: 'bold' }}>
                    {getExecutorDisplayName(selectedSystem.decider)}
                  </div>
                  <div style={{ fontSize: 12, opacity: 0.8, marginTop: 4 }}>
                    {selectedSystem.decider?.type === 'system' ? '嵌套系统' : '独立角色'}
                  </div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small" title="⚡ 行动者" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                <div style={{ textAlign: 'center', color: 'white' }}>
                  <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
                    {selectedSystem.actors.length} 个行动者
                  </div>
                  <Space wrap style={{ justifyContent: 'center' }}>
                    {selectedSystem.actors.slice(0, 3).map((a, i) => (
                      <Tag key={i} color="white" style={{ color: '#f5576c' }}>
                        {a.type === 'system' ? '🔄' : '👤'} {a.name || a.role_id || a.system_id}
                      </Tag>
                    ))}
                  </Space>
                  {selectedSystem.actors.length > 3 && (
                    <div style={{ fontSize: 12, opacity: 0.8, marginTop: 4 }}>
                      还有 {selectedSystem.actors.length - 3} 个...
                    </div>
                  )}
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small" title="🔍 反馈者" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
                <div style={{ textAlign: 'center', color: 'white' }}>
                  <div style={{ fontSize: 24, marginBottom: 8 }}>
                    {selectedSystem.feedbacker?.type === 'system' ? '🔄' : '👤'}
                  </div>
                  <div style={{ fontWeight: 'bold' }}>
                    {getExecutorDisplayName(selectedSystem.feedbacker)}
                  </div>
                  <div style={{ fontSize: 12, opacity: 0.8, marginTop: 4 }}>
                    {selectedSystem.feedbacker?.type === 'system' ? '嵌套系统' : '独立角色'}
                  </div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small" title="📊 状态">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Tag color={selectedSystem.state === 'running' ? 'green' : selectedSystem.state === 'terminated' ? 'red' : 'default'}>
                    {selectedSystem.state}
                  </Tag>
                  <Tag>循环: {selectedSystem.loop_count}</Tag>
                  {selectedSystem.max_loops && <Tag>上限: {selectedSystem.max_loops}</Tag>}
                </Space>
              </Card>
            </Col>
          </Row>

          <Collapse style={{ marginTop: 16 }} defaultActiveKey={['config', 'history']}>
            <Panel header="配置执行者" key="config">
              <Row gutter={16}>
                <Col span={8}>
                  <h4>🎯 决策者</h4>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Select
                      style={{ width: '100%' }}
                      placeholder="选择类型"
                      value={deciderType}
                      onChange={setDeciderType}
                    >
                      <Select.Option value="role">👤 角色</Select.Option>
                      <Select.Option value="system">🔄 系统</Select.Option>
                    </Select>
                    <Select
                      style={{ width: '100%' }}
                      placeholder={`选择${deciderType === 'system' ? '系统' : '角色'}`}
                      onChange={(v) => handleSetDecider(deciderType, v)}
                    >
                      {deciderType === 'role' ? roleExecutors.map(e => (
                        <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
                      )) : systemExecutors.map(e => (
                        <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
                      ))}
                    </Select>
                  </Space>
                </Col>
                <Col span={8}>
                  <h4>⚡ 行动者（可多选）</h4>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Select
                      style={{ width: '100%' }}
                      placeholder="选择类型"
                      value={actorType}
                      onChange={setActorType}
                    >
                      <Select.Option value="role">👤 角色</Select.Option>
                      <Select.Option value="system">🔄 系统</Select.Option>
                    </Select>
                    <Select
                      style={{ width: '100%' }}
                      placeholder={`添加${actorType === 'system' ? '系统' : '角色'}`}
                      onChange={(v) => handleAddActor(actorType, v)}
                    >
                      {actorType === 'role' ? roleExecutors.map(e => (
                        <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
                      )) : systemExecutors.map(e => (
                        <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
                      ))}
                    </Select>
                    <div>
                      {selectedSystem.actors.map((a, idx) => (
                        <Tag
                          key={idx}
                          closable
                          onClose={() => handleRemoveActor(idx)}
                          color={a.type === 'system' ? 'purple' : 'blue'}
                          style={{ marginBottom: 4 }}
                        >
                          {a.type === 'system' ? '🔄' : '👤'} {a.name || a.role_id || a.system_id}
                        </Tag>
                      ))}
                    </div>
                  </Space>
                </Col>
                <Col span={8}>
                  <h4>🔍 反馈者</h4>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Select
                      style={{ width: '100%' }}
                      placeholder="选择类型"
                      value={feedbackerType}
                      onChange={setFeedbackerType}
                    >
                      <Select.Option value="role">👤 角色</Select.Option>
                      <Select.Option value="system">🔄 系统</Select.Option>
                    </Select>
                    <Select
                      style={{ width: '100%' }}
                      placeholder={`选择${feedbackerType === 'system' ? '系统' : '角色'}`}
                      onChange={(v) => handleSetFeedbacker(feedbackerType, v)}
                    >
                      {feedbackerType === 'role' ? roleExecutors.map(e => (
                        <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
                      )) : systemExecutors.map(e => (
                        <Select.Option key={e.value} value={e.value}>{e.label}</Select.Option>
                      ))}
                    </Select>
                  </Space>
                </Col>
              </Row>
              <div style={{ marginTop: 16, padding: 8, background: '#f0f5ff', borderRadius: 4 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  💡 提示：选择「系统」作为执行者将启用分形嵌套，系统将递归执行其内部的决策-行动-反馈循环（最大深度 3）。
                </Text>
              </div>
            </Panel>
            <Panel header="执行历史" key="history">
              {systemSteps.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>
                  暂无执行记录
                </div>
              ) : (
                <Steps
                  direction="vertical"
                  size="small"
                  current={systemSteps.length - 1}
                  items={systemSteps.slice(-5).map((step) => ({
                    title: `第 ${step.step_index} 步`,
                    description: step.terminated
                      ? `已终止: ${step.termination_reason}`
                      : renderStepDetails(step).join(' | '),
                    status: step.terminated ? 'error' : 'finish'
                  }))}
                />
              )}
            </Panel>
          </Collapse>

          <Space style={{ marginTop: 16 }}>
            {selectedSystem.state !== 'running' ? (
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleStart}
                disabled={!canStartSystem}
              >
                启动系统
              </Button>
            ) : (
              <>
                <Button icon={<FastForwardOutlined />} onClick={handleExecuteLoop}>
                  执行一步
                </Button>
                <Button danger icon={<StopOutlined />} onClick={handleStop}>
                  停止
                </Button>
              </>
            )}
          </Space>
        </Card>
      )}
      <ArchitectureGenerator
        open={isGeneratorOpen}
        onClose={() => setIsGeneratorOpen(false)}
      />
    </div>
  )
}