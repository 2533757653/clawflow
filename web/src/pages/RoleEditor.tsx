import { Table, Button, Space, Tag, Tree, Modal, Form, Input, Select, message, Popconfirm, Alert, Checkbox, Spin } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, SwapOutlined, CloudDownloadOutlined, SyncOutlined, BulbOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useStore } from '../stores'
import type { Role, RoleHierarchy } from '../types'
import { roleApi, agencyApi } from '../services/api'
import { roleSuggestionApi } from '../services/roleSuggestionApi'
import SuggestionsModal from '../components/Role/SuggestionsModal'

const { TextArea } = Input

interface TreeNode {
  title: React.ReactNode;
  key: string;
  children?: TreeNode[];
}

export default function RoleEditor() {
  const {
    roles,
    loadRoles,
    createRole,
    updateRole,
    deleteRole,
    loading
  } = useStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isHierarchyModalOpen, setIsHierarchyModalOpen] = useState(false)
  const [isAgencyModalOpen, setIsAgencyModalOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [form] = Form.useForm()
  const [hierarchyData, setHierarchyData] = useState<RoleHierarchy | null>(null)

  const [agencyStatus, setAgencyStatus] = useState<{ is_cloned: boolean; divisions: string[] } | null>(null)
  const [selectedDivisions, setSelectedDivisions] = useState<string[]>([])
  const [isImporting, setIsImporting] = useState(false)
  const [importResult, setImportResult] = useState<{ imported: number; skipped: number } | null>(null)
  const [isSuggestionsModalOpen, setIsSuggestionsModalOpen] = useState(false)
  const [suggestedResponsibilities, setSuggestedResponsibilities] = useState<string[]>([])
  const [isSuggesting, setIsSuggesting] = useState(false)

  useEffect(() => {
    loadRoles()
  }, [loadRoles])

  const handleCreate = async (values: Partial<Role>) => {
    try {
      await createRole(values)
      message.success('角色创建成功')
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      message.error('创建失败')
    }
  }

  const handleUpdate = async (values: Partial<Role>) => {
    if (!editingRole) return
    try {
      await updateRole(editingRole.id, values)
      message.success('角色更新成功')
      setIsModalOpen(false)
      setEditingRole(null)
      form.resetFields()
    } catch {
      message.error('更新失败')
    }
  }

  const handleDelete = async (roleId: string) => {
    try {
      await deleteRole(roleId)
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
    if (roles.length === 0) return
    try {
      const topRole = roles.find(r => !r.reports_to)
      if (topRole) {
        const hierarchy = await roleApi.getHierarchy(topRole.id)
        setHierarchyData(hierarchy)
        setIsHierarchyModalOpen(true)
      } else {
        message.info('没有找到顶级角色')
      }
    } catch {
      message.error('获取层级失败')
    }
  }

  const openAgencyModal = async () => {
    setIsAgencyModalOpen(true)
    setImportResult(null)
    setSelectedDivisions([])
    try {
      const status = await agencyApi.getStatus()
      setAgencyStatus(status)
    } catch {
      message.error('获取 agency-agents 状态失败')
    }
  }

  const handleImport = async () => {
    setIsImporting(true)
    setImportResult(null)
    try {
      const result = await agencyApi.importAgents({
        divisions: selectedDivisions.length > 0 ? selectedDivisions : undefined
      })
      setImportResult({
        imported: result.imported_count,
        skipped: result.skipped_count
      })
      await loadRoles()
      if (result.imported_count > 0) {
        message.success(`成功导入 ${result.imported_count} 个角色`)
      } else if (result.skipped_count > 0) {
        message.info(`已跳过 ${result.skipped_count} 个重复角色`)
      }
    } catch (e) {
      message.error('导入失败: ' + (e as Error).message)
    } finally {
      setIsImporting(false)
    }
  }

  const handleSyncAndImport = async () => {
    try {
      await agencyApi.syncRepo()
      message.success('仓库已同步')
      await openAgencyModal()
    } catch {
      message.error('同步失败')
    }
  }

  const handleSuggestResponsibilities = async () => {
    const values = form.getFieldsValue()
    if (!values.name) {
      message.warning('请先输入角色名称')
      return
    }
    setIsSuggesting(true)
    try {
      const result = await roleSuggestionApi.suggestResponsibilities({
        name: values.name,
        description: values.description,
        division: values.division,
        hierarchy_level: values.hierarchy_level || 1
      })
      setSuggestedResponsibilities(result.data.responsibilities)
      setIsSuggestionsModalOpen(true)
    } catch {
      message.error('获取建议失败')
    } finally {
      setIsSuggesting(false)
    }
  }

  const handleApplySuggestions = (selected: string[]) => {
    form.setFieldsValue({ responsibilities: selected })
    setIsSuggestionsModalOpen(false)
  }

  const handleGenerateSoul = async () => {
    const values = form.getFieldsValue()
    if (!values.name) {
      message.warning('请先输入角色名称')
      return
    }
    try {
      const result = await roleSuggestionApi.generateSoul({
        name: values.name,
        description: values.description,
        division: values.division,
        responsibilities: values.responsibilities || []
      })
      form.setFieldValue('soul_template', result.data.soul_template)
      message.success('Soul 模板已生成')
    } catch {
      message.error('生成 Soul 模板失败')
    }
  }

  const handleSuggestDivision = async () => {
    const values = form.getFieldsValue()
    if (!values.name || !values.description) {
      message.warning('请先输入角色名称和描述')
      return
    }
    try {
      const result = await roleSuggestionApi.suggestDivision({
        name: values.name,
        description: values.description
      })
      if (result.data.suggested_division) {
        form.setFieldValue('division', result.data.suggested_division)
        message.success(`建议部门: ${result.data.suggested_division}`)
      } else {
        message.info('无法确定部门，请手动选择')
      }
    } catch {
      message.error('获取部门建议失败')
    }
  }

  const renderHierarchyTree = (node: RoleHierarchy): TreeNode => ({
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
      key: 'name',
      render: (name: string, record: Role) => (
        <Space>
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

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>角色管理</h2>
        <Space>
          <Button icon={<SwapOutlined />} onClick={showHierarchy}>
            查看层级
          </Button>
          <Button icon={<CloudDownloadOutlined />} onClick={openAgencyModal}>
            从 Agency 导入
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
          <Form.Item name="division" label="部门">
            <Input.Group compact>
              <Form.Item name="division" noStyle>
                <Input placeholder="请输入所属部门" style={{ width: 'calc(100% - 100px)' }} />
              </Form.Item>
              <Button icon={<BulbOutlined />} onClick={handleSuggestDivision}>
                AI 建议
              </Button>
            </Input.Group>
          </Form.Item>
          <Form.Item name="context_memory" label="上下文记忆">
            <TextArea placeholder="请输入角色的上下文记忆内容" rows={4} />
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
            <Input.Group compact>
              <Form.Item name="responsibilities" noStyle>
                <Select mode="tags" placeholder="输入职责后按回车添加" style={{ width: 'calc(100% - 100px)' }}>
                </Select>
              </Form.Item>
              <Button
                icon={<BulbOutlined />}
                onClick={handleSuggestResponsibilities}
                loading={isSuggesting}
              >
                AI 建议
              </Button>
            </Input.Group>
          </Form.Item>
          <Form.Item name="required_skills" label="所需技能" initialValue={[]}>
            <Select mode="tags" placeholder="输入技能后按回车添加">
            </Select>
          </Form.Item>
          <Form.Item name="soul_template" label="Soul 模板">
            <Input.Group compact>
              <Form.Item name="soul_template" noStyle>
                <TextArea placeholder="定义角色的核心价值观、工作风格等" rows={4} style={{ width: 'calc(100% - 120px)' }} />
              </Form.Item>
              <Button icon={<BulbOutlined />} onClick={handleGenerateSoul} style={{ height: 90 }}>
                生成 Soul
              </Button>
            </Input.Group>
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

      <Modal
        title="从 Agency-Agents 导入角色"
        open={isAgencyModalOpen}
        onCancel={() => setIsAgencyModalOpen(false)}
        footer={[
          <Button key="sync" icon={<SyncOutlined />} onClick={handleSyncAndImport}>
            同步仓库
          </Button>,
          <Button key="cancel" onClick={() => setIsAgencyModalOpen(false)}>
            取消
          </Button>,
          <Button
            key="import"
            type="primary"
            loading={isImporting}
            disabled={!agencyStatus?.is_cloned}
            onClick={handleImport}
          >
            导入所选部门 ({selectedDivisions.length})
          </Button>
        ]}
        width={700}
      >
        {!agencyStatus ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin />
            <p>正在加载 agency-agents 状态...</p>
          </div>
        ) : !agencyStatus.is_cloned ? (
          <Alert
            type="warning"
            message="仓库未克隆"
            description="需要先克隆 agency-agents 仓库才能导入角色。点击「同步仓库」按钮开始。"
            showIcon
          />
        ) : (
          <>
            <Alert
              type="info"
              message="agency-agents 包含 144+ 专业 AI Agent，分布在多个部门中。"
              description="选择一个或多个部门进行导入。已存在的角色会被跳过。"
              showIcon
              style={{ marginBottom: 16 }}
            />

            {importResult && (
              <Alert
                type="success"
                message={`导入完成`}
                description={`成功导入 ${importResult.imported} 个角色，跳过 ${importResult.skipped} 个重复角色`}
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <div style={{ marginBottom: 16 }}>
              <Checkbox
                indeterminate={selectedDivisions.length > 0 && selectedDivisions.length < agencyStatus.divisions.length}
                checked={selectedDivisions.length === agencyStatus.divisions.length}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedDivisions([...agencyStatus.divisions])
                  } else {
                    setSelectedDivisions([])
                  }
                }}
              >
                全选 ({agencyStatus.divisions.length})
              </Checkbox>
            </div>

            <div style={{ maxHeight: 400, overflow: 'auto' }}>
              {agencyStatus.divisions.map(division => (
                <div key={division} style={{ marginBottom: 8 }}>
                  <Checkbox
                    checked={selectedDivisions.includes(division)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedDivisions([...selectedDivisions, division])
                      } else {
                        setSelectedDivisions(selectedDivisions.filter(d => d !== division))
                      }
                    }}
                  >
                    {division}
                  </Checkbox>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 16, color: '#666', fontSize: 12 }}>
              <p>注意：导入的角色将包含完整的 SOUL.md 和 IDENTITY.md 模板。</p>
              <p>来源: https://github.com/msitarzewski/agency-agents</p>
            </div>
          </>
        )}
      </Modal>

      <SuggestionsModal
        open={isSuggestionsModalOpen}
        responsibilities={suggestedResponsibilities}
        onApply={handleApplySuggestions}
        onCancel={() => setIsSuggestionsModalOpen(false)}
      />
    </div>
  )
}
