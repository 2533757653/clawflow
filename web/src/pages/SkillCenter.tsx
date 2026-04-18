import { Table, Button, Space, Tag, Input, message, Modal, Tabs } from 'antd'
import { SearchOutlined, DownloadOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useStore } from '../stores'
import type { Skill } from '../types'
import { skillApi } from '../services/api'

export default function SkillCenter() {
  const {
    skills,
    clawhubSkills,
    loadSkills,
    searchClawhubSkills,
    installSkill,
    uninstallSkill,
    loading
  } = useStore()

  const [searchText, setSearchText] = useState('')
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [previewContent, setPreviewContent] = useState('')
  const [activeTab, setActiveTab] = useState('clawhub')

  useEffect(() => {
    loadSkills()
  }, [loadSkills])

  const handleSearch = async () => {
    try {
      await searchClawhubSkills(searchText)
    } catch {
      message.error('搜索失败')
    }
  }

  const handleInstall = async (skillId: string) => {
    try {
      await installSkill(skillId)
      message.success('技能安装成功')
    } catch {
      message.error('安装失败')
    }
  }

  const handleUninstall = async (skillId: string) => {
    try {
      await uninstallSkill(skillId)
      message.success('技能卸载成功')
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
          {record.installed ? (
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleUninstall(record.id)}
            >
              卸载
            </Button>
          ) : (
            <Button
              size="small"
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => handleInstall(record.id)}
            >
              安装
            </Button>
          )}
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
      title: '安装时间',
      dataIndex: 'installed_at',
      key: 'installed_at',
      render: (date: string) => date ? new Date(date).toLocaleString() : '-'
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
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleUninstall(record.id)}
          >
            卸载
          </Button>
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
