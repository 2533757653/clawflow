import { Card, Row, Col, Statistic, List, Tag, Progress } from 'antd';
import { FireOutlined, ClockCircleOutlined, StarOutlined } from '@ant-design/icons';
import type { MemoryStats as MemoryStatsType } from '../../types';

interface MemoryStatsProps {
  stats: MemoryStatsType | null;
}

export default function MemoryStats({ stats }: MemoryStatsProps) {
  if (!stats) {
    return null;
  }

  const typeColors: Record<string, string> = {
    conversation: 'blue',
    fact: 'green',
    preference: 'orange',
    context: 'purple',
    compressed: 'gray'
  };

  return (
    <Card title="记忆统计" size="small">
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="总记忆数"
            value={stats.total_entries}
            prefix={<StarOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="平均重要性"
            value={stats.average_importance}
            precision={2}
            prefix={<FireOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="最新记忆"
            value={stats.newest_entry ? new Date(stats.newest_entry).toLocaleDateString() : 'N/A'}
            prefix={<ClockCircleOutlined />}
          />
        </Col>
      </Row>

      <div style={{ marginTop: 16 }}>
        <h4>记忆类型分布</h4>
        {Object.entries(stats.by_type).map(([type, count]) => {
          const percentage = stats.total_entries > 0
            ? Math.round((count / stats.total_entries) * 100)
            : 0;
          return (
            <div key={type} style={{ marginBottom: 8 }}>
              <Tag color={typeColors[type] || 'default'}>{type}</Tag>
              <span style={{ marginLeft: 8 }}>{count} 条</span>
              <Progress
                percent={percentage}
                size="small"
                showInfo={false}
                strokeColor={typeColors[type] || '#1890ff'}
                style={{ display: 'inline-block', width: 100, marginLeft: 8, verticalAlign: 'middle' }}
              />
            </div>
          );
        })}
      </div>

      {stats.most_accessed && stats.most_accessed.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h4>最常访问的记忆</h4>
          <List
            size="small"
            dataSource={stats.most_accessed.slice(0, 3)}
            renderItem={(item) => (
              <List.Item style={{ padding: '4px 0' }}>
                <span style={{ fontSize: 12 }}>
                  {item.content.substring(0, 50)}
                  {item.content.length > 50 ? '...' : ''}
                </span>
                <Tag color="gold">{item.access_count} 次</Tag>
              </List.Item>
            )}
          />
        </div>
      )}
    </Card>
  );
}
