import { Menu } from 'antd';
import { EditOutlined, CopyOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { Node } from '@xyflow/react';

interface NodeContextMenuProps {
  node: Node;
  position: { x: number; y: number };
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onViewDetails: () => void;
}

export const NodeContextMenu: React.FC<NodeContextMenuProps> = ({
  node: _node,
  position,
  onEdit,
  onDuplicate,
  onDelete,
  onViewDetails
}) => {
  const [contextMenuVisible, setContextMenuVisible] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState(position);

  const handleContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    setContextMenuPosition({ x: event.clientX, y: event.clientY });
    setContextMenuVisible(true);
  };

  const menuItems = [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑节点',
      onClick: onEdit
    },
    {
      key: 'view',
      icon: <EyeOutlined />,
      label: '查看详情',
      onClick: onViewDetails
    },
    {
      key: 'duplicate',
      icon: <CopyOutlined />,
      label: '复制节点',
      onClick: onDuplicate
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除节点',
      danger: true,
      onClick: onDelete
    }
  ];

  return (
    <div onContextMenu={handleContextMenu}>
      <Menu
        items={menuItems}
        onClick={({ key }) => {
          setContextMenuVisible(false);
          switch (key) {
            case 'edit': onEdit(); break;
            case 'duplicate': onDuplicate(); break;
            case 'delete': onDelete(); break;
            case 'view': onViewDetails(); break;
          }
        }}
        openKeys={contextMenuVisible ? ['open'] : []}
        onOpenChange={(openKeys) => setContextMenuVisible(openKeys.length > 0)}
        style={{ position: 'fixed', left: contextMenuPosition.x, top: contextMenuPosition.y }}
      />
    </div>
  );
};