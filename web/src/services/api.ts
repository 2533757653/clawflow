import axios from 'axios';
import type {
  Organization,
  Role,
  Task,
  DataFlow,
  Knowledge,
  Skill,
  RoleHierarchy,
  TaskDependency,
  DeployResult,
  MemoryEntry,
  MemoryCompressionResponse,
  MemoryStats,
  PromptEnhancementResponse,
  RAGQuery,
  RAGResponse,
  RAGStats,
  AgencyStatus,
  AgencyAgentPreview,
  AgencyImportRequest,
  AgencyImportResponse,
  PromptInjectionRequest,
  PromptInjectionResponse,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
});

export const organizationApi = {
  list: () => api.get<Organization[]>('/organizations').then(res => res.data),

  create: (org: Partial<Organization>) =>
    api.post<Organization>('/organizations', org).then(res => res.data),

  get: (id: string) => api.get<Organization>(`/organizations/${id}`).then(res => res.data),

  update: (id: string, org: Partial<Organization>) =>
    api.put<Organization>(`/organizations/${id}`, org).then(res => res.data),

  delete: (id: string) => api.delete(`/organizations/${id}`),

  deploy: (id: string) => api.post<DeployResult>(`/organizations/${id}/deploy`).then(res => res.data),

  start: (id: string) => api.post(`/organizations/${id}/start`),

  stop: (id: string) => api.post(`/organizations/${id}/stop`),
};

export const roleApi = {
  list: () => api.get<Role[]>('/roles').then(res => res.data),

  create: (role: Partial<Role>) =>
    api.post<Role>('/roles', role).then(res => res.data),

  get: (roleId: string) =>
    api.get<Role>(`/roles/${roleId}`).then(res => res.data),

  update: (roleId: string, role: Partial<Role>) =>
    api.put<Role>(`/roles/${roleId}`, role).then(res => res.data),

  delete: (roleId: string) =>
    api.delete(`/roles/${roleId}`),

  getHierarchy: (roleId: string) =>
    api.get<RoleHierarchy>(`/roles/${roleId}/hierarchy`).then(res => res.data),
};

export const taskApi = {
  list: (orgId: string) => api.get<Task[]>(`/organizations/${orgId}/tasks`).then(res => res.data),

  create: (orgId: string, task: Partial<Task>) =>
    api.post<Task>(`/organizations/${orgId}/tasks`, task).then(res => res.data),

  get: (orgId: string, taskId: string) =>
    api.get<Task>(`/organizations/${orgId}/tasks/${taskId}`).then(res => res.data),

  update: (orgId: string, taskId: string, task: Partial<Task>) =>
    api.put<Task>(`/organizations/${orgId}/tasks/${taskId}`, task).then(res => res.data),

  delete: (orgId: string, taskId: string) =>
    api.delete(`/organizations/${orgId}/tasks/${taskId}`),

  getDependencies: (orgId: string, taskId: string) =>
    api.get<TaskDependency>(`/organizations/${orgId}/tasks/${taskId}/dependencies`).then(res => res.data),
};

export const dataflowApi = {
  list: (orgId: string) => api.get<DataFlow[]>(`/organizations/${orgId}/dataflows`).then(res => res.data),

  create: (orgId: string, dataflow: Partial<DataFlow>) =>
    api.post<DataFlow>(`/organizations/${orgId}/dataflows`, dataflow).then(res => res.data),

  get: (orgId: string, dataflowId: string) =>
    api.get<DataFlow>(`/organizations/${orgId}/dataflows/${dataflowId}`).then(res => res.data),

  update: (orgId: string, dataflowId: string, dataflow: Partial<DataFlow>) =>
    api.put<DataFlow>(`/organizations/${orgId}/dataflows/${dataflowId}`, dataflow).then(res => res.data),

  delete: (orgId: string, dataflowId: string) =>
    api.delete(`/organizations/${orgId}/dataflows/${dataflowId}`),
};

export const knowledgeApi = {
  list: (orgId: string) => api.get<Knowledge[]>(`/organizations/${orgId}/knowledge`).then(res => res.data),

  create: (orgId: string, knowledge: Partial<Knowledge>) =>
    api.post<Knowledge>(`/organizations/${orgId}/knowledge`, knowledge).then(res => res.data),

  get: (orgId: string, knowledgeId: string) =>
    api.get<Knowledge>(`/organizations/${orgId}/knowledge/${knowledgeId}`).then(res => res.data),

  update: (orgId: string, knowledgeId: string, knowledge: Partial<Knowledge>) =>
    api.put<Knowledge>(`/organizations/${orgId}/knowledge/${knowledgeId}`, knowledge).then(res => res.data),

  delete: (orgId: string, knowledgeId: string) =>
    api.delete(`/organizations/${orgId}/knowledge/${knowledgeId}`),

  search: (orgId: string, q: string) =>
    api.get<Knowledge[]>(`/organizations/${orgId}/knowledge/search?q=${encodeURIComponent(q)}`).then(res => res.data),

  injectPrompt: (orgId: string, request: PromptInjectionRequest) =>
    api.post<PromptInjectionResponse>(`/organizations/${orgId}/knowledge/inject`, request).then(res => res.data),

  injectSingleKnowledge: (orgId: string, knowledgeId: string, basePrompt: string) =>
    api.post<PromptInjectionResponse>(
      `/organizations/${orgId}/knowledge/inject/${knowledgeId}?base_prompt=${encodeURIComponent(basePrompt)}`
    ).then(res => res.data),
};

export const skillApi = {
  listInstalled: () => api.get<Skill[]>('/skills').then(res => res.data),

  search: (q?: string, tag?: string) => {
    const params = new URLSearchParams();
    if (q) params.append('q', q);
    if (tag) params.append('tag', tag);
    return api.get<Skill[]>(`/skills/search?${params}`).then(res => res.data);
  },

  preview: (skillId: string) =>
    api.get<{ skill_id: string; preview: string }>(`/skills/${skillId}/preview`).then(res => res.data),

  install: (skillId: string) =>
    api.post<Skill>(`/skills/${skillId}/install`).then(res => res.data),

  uninstall: (skillId: string) =>
    api.delete(`/skills/${skillId}/uninstall`),

  installToRole: (skillId: string, roleId: string) =>
    api.post<Skill>(`/skills/${skillId}/install`, { role_id: roleId }).then(res => res.data),

  uninstallSkillFromRole: (skillId: string, roleId: string) =>
    api.delete(`/skills/${skillId}/uninstall/${roleId}`),

  getRoleSkills: (roleId: string) =>
    api.get<Skill[]>(`/skills/role/${roleId}`).then(res => res.data),
};

export const memoryApi = {
  getRoleMemories: (roleId: string) =>
    api.get<MemoryEntry[]>(`/memory/${roleId}`).then(res => res.data),

  addMemory: (roleId: string, content: string, memoryType?: string) =>
    api.post<MemoryEntry>(`/memory/${roleId}`, null, {
      params: { content, memory_type: memoryType || 'conversation' }
    }).then(res => res.data),

  updateMemory: (roleId: string, memoryId: string, content: string) =>
    api.put<MemoryEntry>(`/memory/${roleId}/${memoryId}`, null, { params: { content } }).then(res => res.data),

  deleteMemory: (roleId: string, memoryId: string) =>
    api.delete(`/memory/${roleId}/${memoryId}`),

  accessMemory: (roleId: string, memoryId: string) =>
    api.post<MemoryEntry>(`/memory/${roleId}/access/${memoryId}`).then(res => res.data),

  compressMemories: (roleId: string, maxEntries: number = 10, compressionPrompt?: string) =>
    api.post<MemoryCompressionResponse>(`/memory/compress`, {
      role_id: roleId,
      max_entries: maxEntries,
      compression_prompt: compressionPrompt
    }).then(res => res.data),

  resetMemories: (roleId: string, keepTypes?: string[]) =>
    api.post(`/memory/reset`, {
      role_id: roleId,
      keep_types: keepTypes || ['fact', 'preference']
    }).then(res => res.data),

  getMemoryStats: (roleId: string) =>
    api.get<MemoryStats>(`/memory/${roleId}/stats`).then(res => res.data),

  enhancePromptWithMemory: (roleId: string, basePrompt: string, maxMemoryItems: number = 3) =>
    api.post<PromptEnhancementResponse>(`/memory/enhance-prompt`, {
      role_id: roleId,
      base_prompt: basePrompt,
      max_memory_items: maxMemoryItems
    }).then(res => res.data),

  syncToOpenClaw: (roleId: string, roleName?: string) =>
    api.post(`/memory/${roleId}/sync`, null, { params: { role_name: roleName } }).then(res => res.data),
};

export const ragApi = {
  query: (ragQuery: RAGQuery) =>
    api.post<RAGResponse>('/rag/query', ragQuery).then(res => res.data),

  indexKnowledgeBase: (orgId: string) =>
    api.post<{ knowledge_count: number; total_chunks: number }>(`/rag/index/knowledge-base/${orgId}`).then(res => res.data),

  getStats: () =>
    api.get<RAGStats>('/rag/stats').then(res => res.data),
};

export const agencyApi = {
  getStatus: () =>
    api.get<AgencyStatus>('/agency/status').then(res => res.data),

  getDivisions: () =>
    api.get<string[]>('/agency/divisions').then(res => res.data),

  getDivisionAgents: (division: string) =>
    api.get<AgencyAgentPreview[]>(`/agency/divisions/${division}/agents`).then(res => res.data),

  importAgents: (request?: AgencyImportRequest) =>
    api.post<AgencyImportResponse>('/agency/import', request || {}).then(res => res.data),

  syncRepo: () =>
    api.post('/agency/sync').then(res => res.data),
};
