import { Card, Table, Button, Space, Tag, Modal, Form, Input, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, SearchOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useStore } from '../stores'
import type { Knowledge } from '../types'

const { TextArea } = Input

export default function KnowledgeBase() {
  const {
    currentOrganizationId,
    knowledge,
    loadKnowledge,
    createKnowledge,
    updateKnowledge,
    deleteKnowledge,
    loading
  } = useStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [editingKnowledge, setEditingKnowledge] = useState<Knowledge | null>(null)
  const [previewContent, setPreviewContent] = useState('')
  const [searchText, setSearchText] = useState('')
  const [form] = Form.useForm()

  useEffect(() => {
    if (currentOrganizationId) {
      loadKnowledge(currentOrganizationId)
    }
  }, [currentOrganizationId, loadKnowledge])

  const handleCreate = async (values: Partial<Knowledge>) => {
    if (!currentOrganizationId) {
      message.warning('请先选择一个组织')
      return
    }
    try {
      await createKnowledge(currentOrganizationId, values)
      message.success('知识创建成功')
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      message.error('创建失败')
    }
  }

  const handleUpdate = async (values: Partial<Knowledge>) => {
    if (!currentOrganizationId || !editingKnowledge) return
    try {
      await updateKnowledge(currentOrganizationId, editingKnowledge.id, values)
      message.success('知识更新成功')
      setIsModalOpen(false)
      setEditingKnowledge(null)
      form.resetFields()
    } catch {
      message.error('更新失败')
    }
  }

  const handleDelete = async (knowledgeId: string) => {
    if (!currentOrganizationId) return
    try {
      await deleteKnowledge(currentOrganizationId, knowledgeId)
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  const openEditModal = (kb: Knowledge) => {
    setEditingKnowledge(kb)
    form.setFieldsValue(kb)
    setIsModalOpen(true)
  }

  const openPreview = (kb: Knowledge) => {
    setPreviewContent(kb.content)
    setIsPreviewOpen(true)
  }

  const filteredKnowledge = knowledge.filter(kb =>
    kb.title.toLowerCase().includes(searchText.toLowerCase()) ||
    kb.content.toLowerCase().includes(searchText.toLowerCase()) ||
    (kb.category && kb.category.toLowerCase().includes(searchText.toLowerCase()))
  )

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title'
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => category ? <Tag>{category}</Tag> : <Tag>未分类</Tag>
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <>
          {tags?.map(tag => (
            <Tag key={tag} color="blue" className="skill-tag">{tag}</Tag>
          ))}
        </>
      )
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (v: number) => <Tag>v{v}</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Knowledge) => (
        <Space>
          <Button size="small" onClick={() => openPreview(record)}>
            预览
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)} />
          <Popconfirm
            title="确定删除此知识？"
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
        <Space>
          <h2 style={{ margin: 0 }}>公有知识库</h2>
          <Input
            placeholder="搜索知识..."
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
          />
        </Space>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingKnowledge(null)
            form.resetFields()
            setIsModalOpen(true)
          }}
        >
          添加知识
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={filteredKnowledge}
        rowKey="id"
        loading={loading.knowledge}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingKnowledge ? '编辑知识' : '添加知识'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingKnowledge(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        width={700}
      >
        <Form
          form={form}
          onFinish={editingKnowledge ? handleUpdate : handleCreate}
          layout="vertical"
        >
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input placeholder="请输入知识标题" />
          </Form.Item>
          <Form.Item name="category" label="分类">
            <Select allowClear placeholder="请选择分类">
              <Select.Option value="公司制度">公司制度</Select.Option>
              <Select.Option value="产品文档">产品文档</Select.Option>
              <Select.Option value="技术规范">技术规范</Select.Option>
              <Select.Option value="运营流程">运营流程</Select.Option>
              <Select.Option value="其他">其他</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="tags" label="标签" initialValue={[]}>
            <Select mode="tags" placeholder="输入标签后按回车添加" />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <TextArea placeholder="请输入知识内容" rows={10} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="知识预览"
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
