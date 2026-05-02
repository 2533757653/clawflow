export interface Organization {
  id: string;
  name: string;
  description?: string;
  logo?: string;
  status: 'draft' | 'deployed' | 'running' | 'stopped';
  initial_prompt?: string;
  input_role_id?: string;
  role_ids: string[];
  layout: OrgComponent[];
  created_at: string;
  updated_at: string;
}

export type ComponentType =
  | 'header'
  | 'role_list'
  | 'task_list'
  | 'knowledge'
  | 'data_flow'
  | 'skill'
  | 'prompt'
  | 'memory'
  | 'custom';

export interface OrgComponent {
  id: string;
  type: ComponentType;
  position: { x: number; y: number };
  size: { width: number; height: number };
  config: Record<string, unknown>;
  label?: string;
}

export interface Role {
  id: string;
  name: string;
  description?: string;
  responsibilities: string[];
  required_skills: string[];
  reports_to?: string;
  permission_level: 'admin' | 'manager' | 'member' | 'readonly';
  hierarchy_level: number;
  soul_template?: string;
  identity_template?: string;
  context_memory?: string;
  division?: string;
  source?: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  prompt?: string;
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
  installed_roles: string[];
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

// ─── Memory ───────────────────────────────────────────────────────────────────

export type MemoryType = 'conversation' | 'fact' | 'preference' | 'context' | 'compressed';

export interface MemoryEntry {
  id: string;
  role_id: string;
  content: string;
  memory_type: MemoryType;
  created_at: string;
  access_count: number;
  last_accessed: string | null;
  importance: number;
  tags?: string[];
  parent_id?: string;
  is_compressed?: boolean;
  metadata?: Record<string, unknown>;
}

export interface MemoryCompressionResponse {
  original_count: number;
  compressed_count: number;
  compressed_entries: MemoryEntry[];
  removed_entries: string[];
  summary?: string;
}

export interface MemoryStats {
  total_entries: number;
  by_type: Record<string, number>;
  average_importance: number;
  most_accessed: MemoryEntry[];
  oldest_entry: string | null;
  newest_entry: string | null;
}

export interface PromptEnhancementResponse {
  enhanced_prompt: string;
  memory_used: {
    id: string;
    preview: string;
    importance: number;
  }[];
}

// ─── RAG ──────────────────────────────────────────────────────────────────────

export interface RAGQuery {
  query: string;
  top_k: number;
  organization_id?: string;
  doc_types?: string[];
}

export interface RAGResult {
  chunk_id: string;
  document_id: string;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface RAGResponse {
  query: string;
  results: RAGResult[];
  total_chunks: number;
  processing_time_ms: number;
}

export interface RAGStats {
  total_documents: number;
  total_chunks: number;
  total_embeddings: number;
  documents_by_status: Record<string, number>;
}

export interface SearchResult {
  id: string;
  content: string;
  score: number;
  source: string;
}

// ─── Knowledge ────────────────────────────────────────────────────────────────

export interface PromptInjectionRequest {
  base_prompt: string;
  include_knowledge: boolean;
  max_knowledge_items: number;
}

export interface PromptInjectionResponse {
  enhanced_prompt: string;
  knowledge_used: {
    id: string;
    title: string;
    category: string;
    preview: string;
  }[];
}

// ─── Agency ───────────────────────────────────────────────────────────────────

export interface AgencyImportRequest {
  divisions?: string[];
  agent_names?: string[];
}

export interface AgencyImportResponse {
  imported_count: number;
  skipped_count: number;
  roles: Role[];
  errors: string[];
}

export interface AgencyStatus {
  is_cloned: boolean;
  is_updated: boolean;
  repo_path: string;
  divisions_count: number;
  divisions: string[];
}

export interface AgencyAgentPreview {
  name: string;
  specialty: string;
  description: string;
  division: string;
}
