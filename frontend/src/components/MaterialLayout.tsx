import React, { useState } from 'react';
import {
  Layout,
  Menu,
  Button,
  Typography,
  Space,
  Avatar,
  Divider,
  Tooltip,
  Badge,
  FloatButton
} from 'antd';
import {
  MenuOutlined,
  HomeOutlined,
  FileSearchOutlined,
  SwapOutlined,
  SettingOutlined,
  CompareOutlined,
  BellOutlined,
  UserOutlined,
  InfoCircleOutlined,
  GitHubOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { FilePdf, Layers, Zap } from 'lucide-react';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

interface MaterialLayoutProps {
  children: React.ReactNode;
  selectedMode: 'standard' | 'converter' | 'enhanced';
  onModeChange: (mode: 'standard' | 'converter' | 'enhanced') => void;
}

const MaterialLayout: React.FC<MaterialLayoutProps> = ({
  children,
  selectedMode,
  onModeChange
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);

  const menuItems = [
    {
      key: 'standard',
      icon: <CompareOutlined />,
      label: '标准比对',
      description: '传统DWG文件差异比对',
      color: '#1890ff'
    },
    {
      key: 'converter',
      icon: <FilePdf size={18} />,
      label: 'DWG转换',
      description: '智能PDF转换，支持自然语言',
      color: '#52c41a'
    },
    {
      key: 'enhanced',
      icon: <Layers size={18} />,
      label: '增强比对',
      description: 'AutoCAD驱动的专业比对',
      color: '#722ed1'
    }
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    onModeChange(key as 'standard' | 'converter' | 'enhanced');
    setMobileMenuVisible(false);
  };

  const selectedMenuItem = menuItems.find(item => item.key === selectedMode);

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      {/* 移动端顶部导航栏 */}
      <div className="mobile-header" style={{
        display: 'none',
        padding: '12px 16px',
        background: 'white',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        position: 'sticky',
        top: 0,
        zIndex: 100
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Avatar
              size="small"
              style={{ backgroundColor: '#1890ff' }}
              icon={<CompareOutlined />}
            />
            <Title level={4} style={{ margin: 0, color: '#1890ff' }}>Floor Plan Pro</Title>
          </Space>
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setMobileMenuVisible(!mobileMenuVisible)}
          />
        </div>
      </div>

      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={280}
        style={{
          background: 'white',
          boxShadow: '2px 0 8px rgba(0,0,0,0.06)',
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          zIndex: 99
        }}
      >
        {/* Logo区域 */}
        <div style={{
          padding: '24px 20px',
          borderBottom: '1px solid #f0f0f0',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div style={{ textAlign: 'center' }}>
              <Avatar
                size={collapsed ? 40 : 64}
                style={{
                  backgroundColor: 'white',
                  color: '#667eea',
                  fontSize: collapsed ? '18px' : '28px',
                  fontWeight: 'bold'
                }}
                icon={<CompareOutlined />}
              />
            </div>
            {!collapsed && (
              <div style={{ textAlign: 'center' }}>
                <Title level={4} style={{ margin: 0, color: 'white' }}>
                  Floor Plan Pro
                </Title>
                <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>
                  专业图纸处理工具
                </Text>
              </div>
            )}
          </Space>
        </div>

        {/* 菜单区域 */}
        <Menu
          mode="inline"
          selectedKeys={[selectedMode]}
          onClick={handleMenuClick}
          style={{
            border: 'none',
            padding: '16px 0'
          }}
          items={menuItems.map(item => ({
            key: item.key,
            icon: <span style={{ color: item.color }}>{item.icon}</span>,
            label: (
              <div>
                <div style={{ fontWeight: 500 }}>{item.label}</div>
                {!collapsed && (
                  <Text type="secondary" style={{ fontSize: '11px' }}>
                    {item.description}
                  </Text>
                )}
              </div>
            )
          }))}
        />

        {!collapsed && (
          <>
            <Divider style={{ margin: '16px 20px' }} />

            {/* 快速统计 */}
            <div style={{ padding: '0 20px 16px' }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{
                  padding: '12px',
                  background: '#f6ffed',
                  border: '1px solid #b7eb8f',
                  borderRadius: '8px'
                }}>
                  <Space>
                    <Zap size={16} style={{ color: '#52c41a' }} />
                    <div>
                      <Text strong style={{ color: '#52c41a', fontSize: '12px' }}>
                        高性能处理
                      </Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '11px' }}>
                        AutoCAD 驱动，精准转换
                      </Text>
                    </div>
                  </Space>
                </div>
              </Space>
            </div>

            {/* 底部信息 */}
            <div style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              padding: '16px 20px',
              borderTop: '1px solid #f0f0f0',
              background: 'white'
            }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space split={<Divider type="vertical" />}>
                  <Tooltip title="查看帮助文档">
                    <Button type="text" size="small" icon={<QuestionCircleOutlined />} />
                  </Tooltip>
                  <Tooltip title="GitHub">
                    <Button type="text" size="small" icon={<GitHubOutlined />} />
                  </Tooltip>
                  <Tooltip title="系统信息">
                    <Button type="text" size="small" icon={<InfoCircleOutlined />} />
                  </Tooltip>
                </Space>
                <Text type="secondary" style={{ fontSize: '10px', textAlign: 'center', display: 'block' }}>
                  © 2024 Floor Plan Pro
                </Text>
              </Space>
            </div>
          </>
        )}
      </Sider>

      {/* 主内容区域 */}
      <Layout style={{ marginLeft: collapsed ? 80 : 280, transition: 'all 0.2s' }}>
        {/* 顶部导航栏 */}
        <Header style={{
          background: 'white',
          padding: '0 24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '64px',
          position: 'sticky',
          top: 0,
          zIndex: 98
        }}>
          <Space>
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ fontSize: '16px' }}
            />
            <Divider type="vertical" />
            {selectedMenuItem && (
              <Space>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: selectedMenuItem.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white'
                }}>
                  {selectedMenuItem.icon}
                </div>
                <div>
                  <Title level={4} style={{ margin: 0, color: selectedMenuItem.color }}>
                    {selectedMenuItem.label}
                  </Title>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {selectedMenuItem.description}
                  </Text>
                </div>
              </Space>
            )}
          </Space>

          <Space>
            <Tooltip title="通知">
              <Badge count={0} size="small">
                <Button type="text" icon={<BellOutlined />} />
              </Badge>
            </Tooltip>
            <Tooltip title="用户设置">
              <Avatar size="small" icon={<UserOutlined />} />
            </Tooltip>
          </Space>
        </Header>

        {/* 内容区域 */}
        <Content style={{
          margin: '24px',
          padding: '24px',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
          minHeight: 'calc(100vh - 112px)'
        }}>
          {children}
        </Content>
      </Layout>

      {/* 移动端浮动按钮 */}
      <FloatButton.Group
        trigger="click"
        type="primary"
        style={{ right: 24, bottom: 24 }}
        icon={<MenuOutlined />}
      >
        {menuItems.map(item => (
          <FloatButton
            key={item.key}
            tooltip={item.label}
            icon={item.icon}
            onClick={() => onModeChange(item.key as any)}
            style={{ backgroundColor: item.color }}
          />
        ))}
      </FloatButton.Group>
    </Layout>
  );
};

export default MaterialLayout;