import { Button, message } from 'antd';
import { Node, Edge } from '@xyflow/react';
import dagre from 'dagre';

interface FlowNodeData extends Record<string, unknown> {
  label: string;
  nodeType: string;
  refId?: string;
}

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 172;
  const nodeHeight = 60;

  dagreGraph.setGraph({
    rankdir: 'TB',
    nodesep: 50,
    ranksep: 80
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

interface AutoLayoutButtonProps {
  nodes: Node<FlowNodeData>[];
  edges: Edge[];
  onLayout: (nodes: Node<FlowNodeData>[], edges: Edge[]) => void;
}

export const AutoLayoutButton: React.FC<AutoLayoutButtonProps> = ({ nodes, edges, onLayout }) => {
  const handleAutoLayout = () => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(nodes, edges);
    onLayout(layoutedNodes as Node<FlowNodeData>[], layoutedEdges);
    message.success('已自动排列布局');
  };

  return (
    <Button onClick={handleAutoLayout}>
      自动布局
    </Button>
  );
};