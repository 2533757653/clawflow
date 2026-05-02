import { Table, Button, Space, Tag, Input, message, Modal, Tabs, Select, Popconfirm } from 'antd'
import { SearchOutlined, EyeOutlined, UserAddOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useStore } from '../stores'
import type { Skill } from '../types'
import { skillApi } from '../services/api'

export default function SkillCenter() {
  const {
    skills,
    clawhubSkills,
    roles,
    loadSkills,
    loadRoles,
    searchClawhubSkills,
    loading
  } = useStore()

  const [searchText, setSearchText] = useState('')
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [previewContent, setPreviewContent] = useState('')
  const [activeTab, setActiveTab] = useState('clawhub')
  const [selectedRole, setSelectedRole] = useState<string | null>(null)
  const [isInstallModalOpen, setIsInstallModalOpen] = useState(false)
  const [installingSkill, setInstallingSkill] = useState<Skill | null>(null)

  useEffect(() => {
    loadSkills()
    loadRoles()
  }, [loadSkills, loadRoles])

  const handleSearch = async () => {
    try {
      await searchClawhubSkills(searchText)
    } catch {
      message.error('搜索失败')
    }
  }

  const handleInstall = async (skillId: string, roleId?: string) => {
    try {
      if (roleId) {
        await skillApi.installToRole(skillId, roleId)
        message.success(`技能已安装到角色`)
      }
      setIsInstallModalOpen(false)
      setInstallingSkill(null)
      setSelectedRole(null)
      loadSkills()
    } catch {
      message.error('安装失败')
    }
  }

  const openInstallModal = (skill: Skill) => {
    setInstallingSkill(skill)
    setIsInstallModalOpen(true)
  }

  const handleUninstallFromRole = async (skillId: string, roleId: string) => {
    try {
      await skillApi.uninstallSkillFromRole(skillId, roleId)
      message.success('技能已从角色卸载')
      loadSkills()
    } catch {
      message.error('卸载失败')
    }
  }

  const openPreview = async (skillId: string) => {
    try {
      const result = await skillApi.preview(skillId)
      setPreviewContent(result.preview)
      setIsPreviewOpen(true)
    } catch {
      message.error('获取预览失败')
    }
  }

  const clawhubColumns = [
    {
      title: '技能名称',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (v: string) => <Tag>v{v}</Tag>
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '作者',
      dataIndex: 'author',
      key: 'author',
      render: (a: string) => a || '未知'
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <>
          {tags?.slice(0, 3).map(tag => (
            <Tag key={tag} color="blue" className="skill-tag">{tag}</Tag>
          ))}
          {tags?.length > 3 && <Tag>...</Tag>}
        </>
      )
    },
    {
      title: '状态',
      dataIndex: 'installed',
      key: 'installed',
      render: (installed: boolean) => (
        <Tag color={installed ? 'green' : 'default'}>
          {installed ? '已安装' : '未安装'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Skill) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => openPreview(record.id)}>
            预览
          </Button>
          <Button
            size="small"
            type="primary"
            icon={<UserAddOutlined />}
            onClick={() => openInstallModal(record)}
          >
            安装到角色
          </Button>
        </Space>
      )
    }
  ]

  const installedColumns = [
    {
      title: '技能名称',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (v: string) => <Tag>v{v}</Tag>
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '已安装到',
      dataIndex: 'installed_roles',
      key: 'installed_roles',
      render: (roleIds: string[]) => (
        <Space wrap>
          {roleIds?.length > 0 ? (
            roleIds.map(rid => {
              const role = roles.find(r => r.id === rid)
              return role ? (
                <Tag key={rid} color="blue">{role.name}</Tag>
              ) : null
            })
          ) : (
            <Tag>全局安装</Tag>
          )}
        </Space>
      )
    },
    {
      title: '安装时间',
      dataIndex: 'installed_at',
      key: 'installed_at',
      render: (date: string) => date ? new Date(date).toLocaleString() : '-'
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Skill) => (
        <Space direction="vertical">
          <Space>
            <Button size="small" icon={<EyeOutlined />} onClick={() => openPreview(record.id)}>
              预览
            </Button>
            <Select
              size="small"
              placeholder="添加角色"
              style={{ width: 120 }}
              onChange={async (roleId) => {
                try {
                  await skillApi.installToRole(record.id, roleId)
                  message.success('技能已添加到角色')
                  loadSkills()
                } catch {
                  message.error('添加失败')
                }
              }}
            >
              {roles.map(role => (
                <Select.Option
                  key={role.id}
                  value={role.id}
                  disabled={record.installed_roles.includes(role.id)}
                >
                  {role.name}
                </Select.Option>
              ))}
            </Select>
          </Space>
          {record.installed_roles.length > 0 && (
            <Space wrap>
              {record.installed_roles.map(rid => {
                const role = roles.find(r => r.id === rid)
                return role ? (
                  <Popconfirm
                    key={rid}
                    title={`从 ${role.name} 卸载此技能?`}
                    onConfirm={() => handleUninstallFromRole(record.id, rid)}
                  >
                    <Tag
                      color="orange"
                      style={{ cursor: 'pointer' }}
                      closable
                      onClose={(e) => e.preventDefault()}
                    >
                      {role.name}
                    </Tag>
                  </Popconfirm>
                ) : null
              })}
            </Space>
          )}
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ margin: '0 0 16px 0' }}>技能中心</h2>
        <Space>
          <Input
            placeholder="搜索 ClawHub 技能..."
            prefix={<SearchOutlined />}
            style={{ width: 300 }}
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            onPressEnter={handleSearch}
          />
          <Button type="primary" onClick={handleSearch}>搜索</Button>
        </Space>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'clawhub',
            label: `ClawHub 市场 (${clawhubSkills.length})`,
            children: (
              <Table
                columns={clawhubColumns}
                dataSource={clawhubSkills}
                rowKey="id"
                loading={loading.skills}
                pagination={{ pageSize: 10 }}
              />
            )
          },
          {
            key: 'installed',
            label: `已安装技能 (${skills.length})`,
            children: (
              <Table
                columns={installedColumns}
                dataSource={skills}
                rowKey="id"
                loading={loading.skills}
                pagination={{ pageSize: 10 }}
              />
            )
          }
        ]}
      />

      <Modal
        title="安装技能到角色"
        open={isInstallModalOpen}
        onCancel={() => {
          setIsInstallModalOpen(false)
          setInstallingSkill(null)
          setSelectedRole(null)
        }}
        onOk={() => {
          if (selectedRole && installingSkill) {
            handleInstall(installingSkill.id, selectedRole)
          }
        }}
        okText="安装"
        okButtonProps={{ disabled: !selectedRole || !installingSkill }}
      >
        <div style={{ marginBottom: 16 }}>
          <p>选择要安装技能的角色：</p>
          <Select
            placeholder="请选择角色"
            style={{ width: '100%' }}
            value={selectedRole}
            onChange={setSelectedRole}
          >
            {roles.map(role => (
              <Select.Option key={role.id} value={role.id}>
                {role.name}
              </Select.Option>
            ))}
          </Select>
        </div>
        {installingSkill && (
          <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8 }}>
            <p style={{ margin: 0 }}><strong>技能:</strong> {installingSkill.name}</p>
            <p style={{ margin: '8px 0 0 0' }}><strong>版本:</strong> v{installingSkill.version}</p>
            <p style={{ margin: '8px 0 0 0' }}><strong>描述:</strong> {installingSkill.description}</p>
          </div>
        )}
      </Modal>

      <Modal
        title="技能预览"
        open={isPreviewOpen}
        onCancel={() => setIsPreviewOpen(false)}
        footer={null}
        width={700}
      >
        <div style={{
          background: '#f5f5f5',
          padding: 16,
          borderRadius: 8,
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace',
          maxHeight: 400,
          overflow: 'auto'
        }}>
          {previewContent}
        </div>
      </Modal>
    </div>
  )
}
