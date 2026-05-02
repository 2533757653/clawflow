import { useState } from 'react';
import { Card, Input, Switch, InputNumber, Button, Space, Spin, Divider, message } from 'antd';
import { ExperimentOutlined, ReloadOutlined } from '@ant-design/icons';
import { knowledgeApi } from '../../services/api';
import type { PromptInjectionRequest, PromptInjectionResponse } from '../../types';

const { TextArea } = Input;

interface InjectionPreviewProps {
  orgId: string;
}

export default function InjectionPreview({ orgId }: InjectionPreviewProps) {
  const [basePrompt, setBasePrompt] = useState('');
  const [includeKnowledge, setIncludeKnowledge] = useState(true);
  const [maxKnowledgeItems, setMaxKnowledgeItems] = useState(3);
  const [previewResult, setPreviewResult] = useState<PromptInjectionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handlePreview = async () => {
    if (!basePrompt.trim()) {
      message.warning('请输入 base prompt');
      return;
    }

    setLoading(true);
    try {
      const request: PromptInjectionRequest = {
        base_prompt: basePrompt,
        include_knowledge: includeKnowledge,
        max_knowledge_items: maxKnowledgeItems
      };
      const result = await knowledgeApi.injectPrompt(orgId, request);
      setPreviewResult(result);
    } catch {
      message.error('预览失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setBasePrompt('');
    setPreviewResult(null);
  };

  return (
    <Card
      title={<span><ExperimentOutlined /> Prompt 注入预览</span>}
      extra={
        <Button icon={<ReloadOutlined />} onClick={handleReset} size="small">
          重置
        </Button>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>原始 Prompt</div>
          <TextArea
            placeholder="输入需要增强的 base prompt..."
            value={basePrompt}
            onChange={e => setBasePrompt(e.target.value)}
            rows={4}
            style={{ fontFamily: 'monospace' }}
          />
        </div>

        <Space>
          <span>包含知识库:</span>
          <Switch checked={includeKnowledge} onChange={setIncludeKnowledge} />
          <InputNumber
            value={maxKnowledgeItems}
            onChange={(v: number | null) => setMaxKnowledgeItems(v || 3)}
            min={1}
            max={10}
            disabled={!includeKnowledge}
            addonAfter="条"
          />
        </Space>

        <Button
          type="primary"
          onClick={handlePreview}
          loading={loading}
          disabled={!basePrompt.trim()}
        >
          生成预览
        </Button>

        {loading && <Spin tip="正在生成预览..." />}

        {previewResult && (
          <>
            <Divider orientation="left">增强后的 Prompt</Divider>
            <div style={{
              background: '#f0f0f0',
              padding: 16,
              borderRadius: 8,
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              fontSize: 13,
              maxHeight: 400,
              overflow: 'auto',
              border: '1px solid #d9d9d9'
            }}>
              {previewResult.enhanced_prompt}
            </div>

            {previewResult.knowledge_used.length > 0 && (
              <>
                <Divider orientation="left">使用的知识 ({previewResult.knowledge_used.length} 条)</Divider>
                {previewResult.knowledge_used.map((k, i) => (
                  <Card key={k.id} size="small" style={{ marginBottom: 8 }}>
                    <div style={{ fontWeight: 500 }}>{i + 1}. {k.title}</div>
                    {k.category && <div style={{ color: '#666', fontSize: 12 }}>分类: {k.category}</div>}
                    <div style={{ color: '#888', fontSize: 12, marginTop: 4 }}>
                      {k.preview}
                    </div>
                  </Card>
                ))}
              </>
            )}
          </>
        )}
      </Space>
    </Card>
  );
}
