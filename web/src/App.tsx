import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Menu, Typography, theme } from 'antd'
import {
  AppstoreOutlined,
  TeamOutlined,
  PartitionOutlined,
  DatabaseOutlined,
  ToolOutlined,
  RocketOutlined,
  SettingOutlined,
  AimOutlined
} from '@ant-design/icons'
import { useEffect } from 'react'
import { useStore } from './stores'
import Dashboard from './pages/Dashboard'
import RoleEditor from './pages/RoleEditor'
import TaskEditor from './pages/TaskEditor'
import DataFlowEditor from './pages/DataFlowEditor'
import KnowledgeBase from './pages/KnowledgeBase'
import SkillCenter from './pages/SkillCenter'
import OrganizationEditor from './pages/OrganizationEditor'
import SystemEditor from './pages/SystemEditor'

const { Header, Sider, Content } = Layout
const { Title } = Typography

function App() {
  const { loadOrganizations, loadSkills } = useStore()
  const {
    token: { colorBgContainer, borderRadiusLG }
  } = theme.useToken()

  useEffect(() => {
    loadOrganizations()
    loadSkills()
  }, [loadOrganizations, loadSkills])

  const menuItems = [
    {
      key: '/',
      icon: <AppstoreOutlined />,
      label: '组织概览'
    },
    {
      key: '/organization',
      icon: <SettingOutlined />,
      label: '组织设置'
    },
    {
      key: '/roles',
      icon: <TeamOutlined />,
      label: '角色管理'
    },
    {
      key: '/tasks',
      icon: <PartitionOutlined />,
      label: '任务管理'
    },
    {
      key: '/dataflows',
      icon: <DatabaseOutlined />,
      label: '数据流设计'
    },
    {
      key: '/systems',
      icon: <AimOutlined />,
      label: '决策系统'
    },
    {
      key: '/knowledge',
      icon: <DatabaseOutlined />,
      label: '知识库'
    },
    {
      key: '/skills',
      icon: <ToolOutlined />,
      label: '技能中心'
    }
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px', background: '#001529' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginRight: 40 }}>
          <RocketOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 12 }} />
          <Title level={4} style={{ color: 'white', margin: 0 }}>ClawFlow</Title>
        </div>
        <Title level={5} style={{ color: 'rgba(255,255,255,0.65)', margin: 0 }}>
          Agent 组织动态构建平台
        </Title>
      </Header>
      <Layout>
        <Sider width={220} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            defaultSelectedKeys={['/']}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        <Layout style={{ padding: '0 24px 24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/organization" element={<OrganizationEditor />} />
              <Route path="/roles" element={<RoleEditor />} />
              <Route path="/tasks" element={<TaskEditor />} />
              <Route path="/dataflows" element={<DataFlowEditor />} />
              <Route path="/systems" element={<SystemEditor />} />
              <Route path="/knowledge" element={<KnowledgeBase />} />
              <Route path="/skills" element={<SkillCenter />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default App
