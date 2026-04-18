export interface Organization {
  id: string;
  name: string;
  description?: string;
  logo?: string;
  status: 'draft' | 'deployed' | 'running' | 'stopped';
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  responsibilities: string[];
  required_skills: string[];
  reports_to?: string;
  permission_level: 'admin' | 'manager' | 'member' | 'readonly';
  hierarchy_level: number;
  soul_template?: string;
  identity_template?: string;
  agents_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  assigned_role_id?: string;
  dependencies: string[];
  priority: 'high' | 'medium' | 'low';
  execution_mode: 'sequential' | 'parallel' | 'conditional';
  conditions: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DataFlowNode {
  id: string;
  type: 'role' | 'task' | 'knowledge' | 'input' | 'output';
  ref_id?: string;
  position: { x: number; y: number };
  label?: string;
}

export interface DataFlowEdge {
  id: string;
  source: string;
  target: string;
  data_mapping: Record<string, unknown>;
  condition?: string;
}

export interface DataFlow {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  nodes: DataFlowNode[];
  edges: DataFlowEdge[];
  created_at: string;
  updated_at: string;
}

export interface Knowledge {
  id: string;
  organization_id: string;
  title: string;
  content: string;
  category?: string;
  tags: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Skill {
  id: string;
  name: string;
  version: string;
  description?: string;
  author?: string;
  tags: string[];
  installed: boolean;
  installed_at?: string;
  local_path?: string;
}

export interface RoleHierarchy {
  id: string;
  name: string;
  description?: string;
  hierarchy_level: number;
  permission_level: string;
  children: RoleHierarchy[];
  circular_reference?: boolean;
}

export interface TaskDependency {
  id: string;
  name: string;
  description?: string;
  priority: string;
  execution_mode: string;
  dependencies: TaskDependency[];
  circular_reference?: boolean;
}

export interface DeployResult {
  message: string;
  deployed_agents: {
    role_id: string;
    role_name: string;
    deployed_at: string;
  }[];
  total_roles: number;
}

export type ExecutorType = 'role' | 'system';

export interface ExecutorUnit {
  type: ExecutorType;
  role_id?: string;
  system_id?: string;
  depth: number;
  name?: string;
}

export interface SystemNode {
  role_id: string;
  role_type: 'decider' | 'actor' | 'feedbacker';
  config: Record<string, unknown>;
}

export interface SystemEdge {
  source_id: string;
  target_id: string;
  edge_type: string;
  data_mapping: Record<string, unknown>;
}

export interface AgentSystem {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  decider?: ExecutorUnit;
  actors: ExecutorUnit[];
  feedbacker?: ExecutorUnit;
  nodes: SystemNode[];
  edges: SystemEdge[];
  state: 'initialized' | 'running' | 'stopped' | 'terminated';
  loop_count: number;
  max_loops?: number;
  max_depth: number;
  created_at: string;
  updated_at: string;
}

export interface SystemLoopStep {
  id: string;
  system_id: string;
  step_index: number;
  phase: string;
  depth: number;
  executor_type?: string;
  executor_name?: string;
  decider_output?: Record<string, unknown>;
  actor_output?: Record<string, unknown>;
  feedbacker_output?: Record<string, unknown>;
  terminated: boolean;
  termination_reason?: string;
  child_steps: SystemLoopStep[];
  created_at: string;
}

export interface AvailableExecutors {
  roles: { id: string; name: string; type: 'role' }[];
  systems: { id: string; name: string; type: 'system' }[];
}

export interface GeneratedRole {
  name: string;
  description: string;
  responsibilities: string[];
  role_type: string;
  hierarchy_level: number;
}

export interface GeneratedActor {
  name: string;
  is_nested_system: boolean;
  nested_roles: GeneratedRole[];
  is_group: boolean;
  group_members: string[];
}

export interface GeneratedSystem {
  name: string;
  description: string;
  template_type: 'simple' | 'hierarchical' | 'parallel';
  decider: GeneratedRole;
  actors: GeneratedActor[];
  feedbacker: GeneratedRole;
  nested_systems: GeneratedSystem[];
}

export interface GenerateRequest {
  description: string;
  org_id?: string;
}

export interface GenerateResponse {
  roles: GeneratedRole[];
  systems: GeneratedSystem[];
  suggestions: string[];
}
