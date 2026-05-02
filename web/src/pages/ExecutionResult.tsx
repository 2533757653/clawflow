import { Card, Row, Col, Statistic, Button, Tag, Space, message, Modal, Form, Input, Timeline, Alert, Spin } from 'antd'
import { PlayCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useStore } from '../stores'
import { executionApi, type ExecutionResult, type ExecuteRequest } from '../services/executionApi'

const { TextArea } = Input

export default function ExecutionResult() {
  const { currentOrganizationId, organizations } = useStore()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)

  const currentOrg = organizations.find(o => o.id === currentOrganizationId)

  const handleExecute = async (values: { user_input: string }) => {
    if (!currentOrganizationId) {
      message.error('请先选择一个组织')
      return
    }

    setIsExecuting(true)
    setExecutionResult(null)

    try {
      const request: ExecuteRequest = {
        input_data: { user_input: values.user_input }
      }
      const result = await executionApi.execute(currentOrganizationId, request)
      setExecutionResult(result)
      message.success('执行完成')
    } catch (e) {
      message.error('执行失败: ' + (e as Error).message)
    } finally {
      setIsExecuting(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'partial':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />
      default:
        return <ClockCircleOutlined />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      case 'partial':
        return 'warning'
      default:
        return 'default'
    }
  }

  const totalExecutionTime = executionResult?.node_results.reduce((sum, n) => sum + n.execution_time_ms, 0) || 0

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <h2 style={{ margin: 0 }}>工作流执行</h2>
          {currentOrg && (
            <Tag color="blue">{currentOrg.name}</Tag>
          )}
        </Space>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={() => setIsModalOpen(true)}
          disabled={!currentOrganizationId}
        >
          执行工作流
        </Button>
      </div>

      {!currentOrganizationId && (
        <Alert
          type="warning"
          message="请先在仪表盘选择一个组织"
          description="执行工作流前需要选择一个组织"
          showIcon
        />
      )}

      {executionResult && (
        <>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="执行状态"
                  value={executionResult.status.toUpperCase()}
                  prefix={getStatusIcon(executionResult.status)}
                  valueStyle={{ color: getStatusColor(executionResult.status) === 'success' ? '#52c41a' : getStatusColor(executionResult.status) === 'error' ? '#ff4d4f' : '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="执行节点数"
                  value={executionResult.node_results.length}
                  prefix={<ThunderboltOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总执行时间"
                  value={totalExecutionTime}
                  suffix="ms"
                  prefix={<ClockCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="执行ID"
                  value={executionResult.execution_id.slice(0, 8) + '...'}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={16}>
              <Card title="节点执行详情">
                <Timeline
                  items={executionResult.node_results.map((node) => ({
                    color: node.error ? 'red' : 'green',
                    children: (
                      <div>
                        <Space>
                          <Tag>{node.node_id.slice(0, 8)}</Tag>
                          {node.role_id && <Tag color="blue">Role: {node.role_id.slice(0, 8)}</Tag>}
                          {node.task_id && <Tag color="purple">Task: {node.task_id.slice(0, 8)}</Tag>}
                          <Tag>{node.execution_time_ms}ms</Tag>
                          {node.error && <Tag color="red">{node.error}</Tag>}
                        </Space>
                        {node.output && (
                          <div style={{ marginTop: 8, background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                            <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                              {JSON.stringify(node.output, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )
                  }))}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card title="最终输出">
                {Object.keys(executionResult.final_output).length > 0 ? (
                  <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(executionResult.final_output, null, 2)}
                  </pre>
                ) : (
                  <Alert message="没有最终输出" type="info" showIcon />
                )}
              </Card>
            </Col>
          </Row>
        </>
      )}

      <Modal
        title="执行工作流"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
        }}
        footer={null}
        width={600}
      >
        {isExecuting ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
            <p>正在执行工作流...</p>
          </div>
        ) : (
          <Form form={form} onFinish={handleExecute} layout="vertical">
            <Alert
              type="info"
              message={`组织: ${currentOrg?.name || '未选择'}`}
              description="请输入您想要执行的指令或问题"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Form.Item
              name="user_input"
              label="输入指令"
              rules={[{ required: true, message: '请输入指令' }]}
            >
              <TextArea
                placeholder="请输入要执行的指令或问题..."
                rows={4}
              />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />}>
                  执行
                </Button>
                <Button onClick={() => {
                  setIsModalOpen(false)
                  form.resetFields()
                }}>
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}