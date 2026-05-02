import { useEffect } from 'react';
import { Card, Statistic, Row, Col, Button, Space, Tag, Spin, message } from 'antd';
import { DatabaseOutlined, FileTextOutlined, BranchesOutlined, ReloadOutlined } from '@ant-design/icons';
import { useStore } from '../../stores';

interface IndexStatusProps {
  orgId: string;
}

export default function IndexStatus({ orgId }: IndexStatusProps) {
  const { ragStats, loadRagStats, reindexKnowledgeBase, loading } = useStore();

  useEffect(() => {
    loadRagStats();
  }, [loadRagStats]);

  const handleReindex = async () => {
    try {
      const result = await reindexKnowledgeBase(orgId);
      message.success(`索引完成: ${result.knowledge_count} 条知识, ${result.total_chunks} 个 chunks`);
    } catch {
      message.error('索引失败');
    }
  };

  if (!ragStats && loading.rag) {
    return (
      <Card>
        <Spin tip="加载索引状态..." />
      </Card>
    );
  }

  const statusColor = ragStats && ragStats.total_documents > 0 ? 'green' : 'orange';
  const statusText = ragStats && ragStats.total_documents > 0 ? '已索引' : '未索引';

  return (
    <Card
      title={<span><DatabaseOutlined /> 索引状态</span>}
      extra={
        <Button
          icon={<ReloadOutlined />}
          onClick={handleReindex}
          loading={loading.rag}
          size="small"
        >
          重建索引
        </Button>
      }
    >
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="文档数"
            value={ragStats?.total_documents || 0}
            prefix={<FileTextOutlined />}
            valueStyle={{ color: '#3f8600' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Chunks"
            value={ragStats?.total_chunks || 0}
            prefix={<BranchesOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Embeddings"
            value={ragStats?.total_embeddings || 0}
            prefix={<DatabaseOutlined />}
            valueStyle={{ color: '#722ed1' }}
          />
        </Col>
      </Row>

      <div style={{ marginTop: 16 }}>
        <Space>
          <Tag color={statusColor}>{statusText}</Tag>
          {ragStats?.documents_by_status && Object.keys(ragStats.documents_by_status).length > 0 && (
            <>
              {Object.entries(ragStats.documents_by_status).map(([status, count]) => (
                <Tag key={status}>{status}: {count}</Tag>
              ))}
            </>
          )}
        </Space>
      </div>
    </Card>
  );
}
