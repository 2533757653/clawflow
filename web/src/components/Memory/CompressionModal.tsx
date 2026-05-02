import { Modal, Form, InputNumber, Input, Button, Result, Space, Alert } from 'antd';
import { useState } from 'react';
import type { MemoryCompressionResponse } from '../../types';

const { TextArea } = Input;

interface CompressionModalProps {
  open: boolean;
  onCancel: () => void;
  roleId: string;
  onConfirm: (maxEntries: number, compressionPrompt?: string) => Promise<MemoryCompressionResponse>;
}

export default function CompressionModal({
  open,
  onCancel,
  onConfirm
}: CompressionModalProps) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MemoryCompressionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      setError(null);
      const response = await onConfirm(values.maxEntries, values.compressionPrompt);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : '压缩失败');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setResult(null);
    setError(null);
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="压缩记忆"
      open={open}
      onCancel={handleClose}
      footer={
        result ? (
          <Button type="primary" onClick={handleClose}>
            完成
          </Button>
        ) : (
          <Space>
            <Button onClick={handleClose}>取消</Button>
            <Button type="primary" loading={loading} onClick={handleOk}>
              确认压缩
            </Button>
          </Space>
        )
      }
      width={600}
    >
      {error && (
        <Alert
          message="压缩失败"
          description={error}
          type="error"
          style={{ marginBottom: 16 }}
          showIcon
        />
      )}

      {result ? (
        <Result
          status="success"
          title="压缩完成"
          subTitle={`已从 ${result.original_count} 条记忆中保留 ${result.compressed_count} 条`}
          extra={[
            <div key="details">
              <h4>被移除的记忆 ID:</h4>
              <ul>
                {result.removed_entries.map(id => (
                  <li key={id}>{id}</li>
                ))}
              </ul>
            </div>
          ]}
        />
      ) : (
        <>
          <Alert
            message="记忆压缩说明"
            description="压缩将根据重要性保留最重要的记忆条目。被标记为压缩的记忆仍会保留原始内容，但会被归档。"
            type="info"
            style={{ marginBottom: 16 }}
            showIcon
          />

          <Form
            form={form}
            layout="vertical"
            initialValues={{
              maxEntries: 10,
              compressionPrompt: ''
            }}
          >
            <Form.Item
              name="maxEntries"
              label="保留记忆数量"
              rules={[{ required: true, message: '请输入保留数量' }]}
            >
              <InputNumber min={1} max={100} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="compressionPrompt"
              label="压缩提示 (可选)"
              tooltip="用于生成压缩摘要的提示词"
            >
              <TextArea
                rows={3}
                placeholder="例如: 总结这轮对话的主要内容和关键决策..."
              />
            </Form.Item>
          </Form>
        </>
      )}
    </Modal>
  );
}
