import { useState } from 'react';
import { Input, List, Tag, Empty, Segmented } from 'antd';
import { SearchOutlined, BulbOutlined } from '@ant-design/icons';
import { useStore } from '../../stores';
import type { SearchResult } from '../../types';

interface SearchPanelProps {
  orgId: string;
}

function highlightText(text: string, keyword: string): React.ReactNode {
  if (!keyword) return text;
  const parts = text.split(new RegExp(`(${keyword})`, 'gi'));
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === keyword.toLowerCase() ? (
          <span key={i} style={{ backgroundColor: '#ffe58f', padding: '0 2px' }}>{part}</span>
        ) : (
          part
        )
      )}
    </>
  );
}

export default function SearchPanel({ orgId }: SearchPanelProps) {
  const [searchType, setSearchType] = useState<'keyword' | 'semantic'>('keyword');
  const [query, setQuery] = useState('');
  const [keywordResults, setKeywordResults] = useState<import('../../types').Knowledge[]>([]);
  const [semanticResults, setSemanticResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  const { knowledge, semanticSearch, ragStats } = useStore();

  const handleKeywordSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const results = await Promise.resolve(
        knowledge.filter(kb =>
          kb.title.toLowerCase().includes(query.toLowerCase()) ||
          kb.content.toLowerCase().includes(query.toLowerCase()) ||
          (kb.category && kb.category.toLowerCase().includes(query.toLowerCase())) ||
          kb.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
        )
      );
      setKeywordResults(results);
    } finally {
      setSearching(false);
    }
  };

  const handleSemanticSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const results = await semanticSearch(query, orgId, 10);
      setSemanticResults(results);
    } finally {
      setSearching(false);
    }
  };

  const handleSearch = () => {
    if (searchType === 'keyword') {
      handleKeywordSearch();
    } else {
      handleSemanticSearch();
    }
  };

  return (
    <div style={{ padding: 16 }}>
      <div style={{ marginBottom: 16 }}>
        <Segmented
          value={searchType}
          onChange={(v) => setSearchType(v as 'keyword' | 'semantic')}
          options={[
            { label: '关键词搜索', value: 'keyword' },
            { label: '语义搜索', value: 'semantic' },
          ]}
          style={{ marginBottom: 12 }}
        />
        <Input.Search
          placeholder={searchType === 'keyword' ? '搜索知识...' : '输入问题进行语义搜索...'}
          value={query}
          onChange={e => setQuery(e.target.value)}
          onSearch={handleSearch}
          loading={searching}
          enterButton={
            searchType === 'semantic' ? (
              <span><BulbOutlined /> 搜索</span>
            ) : (
              <span><SearchOutlined /> 搜索</span>
            )
          }
        />
      </div>

      {ragStats && (
        <div style={{ marginBottom: 16, fontSize: 12, color: '#666' }}>
          <Tag color="blue">索引状态</Tag>
          文档: {ragStats.total_documents} | Chunks: {ragStats.total_chunks} | Embeddings: {ragStats.total_embeddings}
        </div>
      )}

      {searchType === 'semantic' ? (
        <List
          loading={searching}
          locale={{ emptyText: <Empty description="输入查询词进行语义搜索" /> }}
          dataSource={semanticResults}
          renderItem={(item: SearchResult) => (
            <List.Item>
              <List.Item.Meta
                title={
                  <span>
                    {item.source}
                    <Tag color="green" style={{ marginLeft: 8 }}>
                      相似度: {(item.score * 100).toFixed(1)}%
                    </Tag>
                  </span>
                }
                description={
                  <div style={{ background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                    {highlightText(item.content, query)}
                  </div>
                }
              />
            </List.Item>
          )}
        />
      ) : (
        <List
          loading={searching}
          locale={{ emptyText: <Empty description="输入关键词搜索知识" /> }}
          dataSource={keywordResults}
          renderItem={(item: import('../../types').Knowledge) => (
            <List.Item>
              <List.Item.Meta
                title={
                  <span>
                    {highlightText(item.title, query)}
                    {item.category && <Tag color="blue" style={{ marginLeft: 8 }}>{item.category}</Tag>}
                  </span>
                }
                description={
                  <div>
                    {item.tags.map(tag => (
                      <Tag key={tag} style={{ marginTop: 4 }}>{highlightText(tag, query)}</Tag>
                    ))}
                    <div style={{ marginTop: 8, background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                      {highlightText(item.content.slice(0, 200) + (item.content.length > 200 ? '...' : ''), query)}
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  );
}
