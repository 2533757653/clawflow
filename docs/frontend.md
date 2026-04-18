# ClawFlow 前端文档

## 技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2.0 | UI 框架 |
| Ant Design | 5.12.0 | UI 组件库 |
| Axios | 1.6.2 | HTTP 客户端 |
| Babel | 7.23.5 | JSX 编译 (运行时) |

## 架构设计

### 单文件架构 (SPA)

前端代码完全内嵌在 `api/main.py` 的 Python 字符串中，通过 FastAPI 的 `FileResponse` 直接返回 HTML 文件。

**优点**：
- 无需构建工具
- 一条命令启动前后端
- 部署简单

**缺点**：
- 不适合复杂应用
- 性能略低于打包方案

### 状态管理

使用 React Hooks (`useState`, `useEffect`) 进行状态管理：

```jsx
const [currentOrg, setCurrentOrg] = useState(null);
const [roles, setRoles] = useState([]);
```

### 组件结构

```
App
├── Header (Header)
├── Sider (Menu)
│   └── MenuItem
└── Content
    ├── Dashboard
    ├── RoleEditor
    ├── TaskEditor
    ├── DataFlowEditor
    ├── KnowledgeBase
    ├── SkillCenter
    └── OrganizationSettings
```

## 页面组件

### 1. Dashboard (组织概览)

**功能**：
- 显示组织列表
- 统计信息（总数、已部署、草稿、角色数）
- 创建组织
- 部署/删除组织

**状态**：
```jsx
const [currentOrg, setCurrentOrg] = useState(null);
const [orgs, setOrgs] = useState([]);
const [roles, setRoles] = useState([]);
```

### 2. RoleEditor (角色管理)

**功能**：
- 角色 CRUD
- 层级设置
- 汇报关系
- 角色层级树视图

**核心代码**：
```jsx
function buildHierarchyTree(roles, parentId = null) {
    return roles
        .filter(r => r.reports_to === parentId)
        .map(r => ({
            title: <span>{r.name} <Tag>L{r.hierarchy_level}</Tag></span>,
            key: r.id,
            children: buildHierarchyTree(roles, r.id)
        }));
}
```

### 3. TaskEditor (任务管理)

**功能**：
- 任务 CRUD
- 优先级设置
- 执行模式配置
- 依赖关系管理

### 4. DataFlowEditor (数据流设计)

**功能**：
- 数据流 CRUD
- 可视化节点设计器
- 节点类型：role, task, knowledge, input, output

**节点样式**：
```css
.flow-node { position: absolute; padding: 12px 16px; border-radius: 8px; }
.flow-node.role { background: #e6f7ff; border: 2px solid #1890ff; }
.flow-node.task { background: #fff7e6; border: 2px solid #fa8c16; }
.flow-node.knowledge { background: #f6ffed; border: 2px solid #52c41a; }
.flow-node.input, .flow-node.output { background: #f0f5ff; border: 2px solid #722ed1; }
```

### 5. KnowledgeBase (知识库)

**功能**：
- 知识条目 CRUD
- 分类管理
- 标签管理
- 搜索功能

### 6. SkillCenter (技能中心)

**功能**：
- ClawHub 技能搜索
- 已安装技能列表
- 技能安装/卸载

**Tabs**：
```jsx
<Tabs items={[
    { key: 'clawhub', label: 'ClawHub 市场', children: <Table ... /> },
    { key: 'installed', label: '已安装', children: <Table ... /> }
]} />
```

### 7. OrganizationSettings (组织设置)

**功能**：
- 基本信息编辑
- 部署管理
- 状态显示

## API 通信

### Axios 实例

```javascript
const API = '/api/v1';

// 异步请求包装
const api = {
    async listOrgs() {
        const r = await axios.get(`${API}/organizations`);
        return r.data;
    },
    async createOrg(org) {
        const r = await axios.post(`${API}/organizations`, org);
        return r.data;
    },
    // ...
};
```

### 错误处理

```jsx
try {
    await axios.post(`${API}/organizations`, values);
    message.success('创建成功');
} catch () {
    message.error('创建失败');
}
```

## UI 组件使用

### 布局组件

```jsx
<Layout>
    <Header>Header</Header>
    <Layout>
        <Sider>Sider</Sider>
        <Content>Content</Content>
    </Layout>
</Layout>
```

### 表单组件

```jsx
<Form form={form} onFinish={handleCreate} layout="vertical">
    <Form.Item name="name" label="名称" rules={[{ required: true }]}>
        <Input />
    </Form.Item>
    <Form.Item name="tags" label="标签">
        <Select mode="tags">{...}</Select>
    </Form.Item>
</Form>
```

### 表格组件

```jsx
<Table
    columns={columns}
    dataSource={data}
    rowKey="id"
    pagination={{ pageSize: 10 }}
/>
```

## 样式说明

### 全局样式

```css
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
#root { min-height: 100vh; }
```

### 组件样式

| 类名 | 用途 |
|------|------|
| `.page-header` | 页面标题栏 |
| `.page-title` | 页面标题 |
| `.card-grid` | 卡片网格布局 |
| `.org-card` | 组织卡片 |
| `.empty-state` | 空状态提示 |
| `.flow-canvas` | 数据流画布 |
| `.flow-node` | 数据流节点 |

## 启动流程

1. 浏览器访问 `http://localhost:8000`
2. FastAPI 返回 `index.html`
3. React 加载并渲染 App 组件
4. App 组件调用 `refreshOrgs()` 获取组织列表
5. 用户交互触发 API 调用

## CDN 资源

```html
<link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/antd/5.12.0/reset.min.css">
<script src="https://cdn.bootcdn.net/ajax/libs/react/18.2.0/umd/react.production.min.js"></script>
<script src="https://cdn.bootcdn.net/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js"></script>
<script src="https://cdn.bootcdn.net/ajax/libs/babel-standalone/7.23.5/babel.min.js"></script>
<script src="https://cdn.bootcdn.net/ajax/libs/antd/5.12.0/antd.min.js"></script>
<script src="https://cdn.bootcdn.net/ajax/libs/axios/1.6.2/axios.min.js"></script>
```
