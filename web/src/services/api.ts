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
  AgentSystem,
  SystemLoopStep,
  ExecutorUnit,
  AvailableExecutors,
  GenerateRequest,
  GenerateResponse
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

  undeploy: (id: string) => api.post(`/organizations/${id}/undeploy`),
};

export const roleApi = {
  list: (orgId: string) => api.get<Role[]>(`/organizations/${orgId}/roles`).then(res => res.data),

  create: (orgId: string, role: Partial<Role>) =>
    api.post<Role>(`/organizations/${orgId}/roles`, role).then(res => res.data),

  get: (orgId: string, roleId: string) =>
    api.get<Role>(`/organizations/${orgId}/roles/${roleId}`).then(res => res.data),

  update: (orgId: string, roleId: string, role: Partial<Role>) =>
    api.put<Role>(`/organizations/${orgId}/roles/${roleId}`, role).then(res => res.data),

  delete: (orgId: string, roleId: string) =>
    api.delete(`/organizations/${orgId}/roles/${roleId}`),

  getHierarchy: (orgId: string, roleId: string) =>
    api.get<RoleHierarchy>(`/organizations/${orgId}/roles/${roleId}/hierarchy`).then(res => res.data),
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
};

export const systemApi = {
  list: (orgId: string) => api.get<AgentSystem[]>(`/organizations/${orgId}/systems`).then(res => res.data),

  create: (orgId: string, system: Partial<AgentSystem>) =>
    api.post<AgentSystem>(`/organizations/${orgId}/systems`, system).then(res => res.data),

  get: (orgId: string, systemId: string) =>
    api.get<AgentSystem>(`/organizations/${orgId}/systems/${systemId}`).then(res => res.data),

  update: (orgId: string, systemId: string, system: Partial<AgentSystem>) =>
    api.put<AgentSystem>(`/organizations/${orgId}/systems/${systemId}`, system).then(res => res.data),

  delete: (orgId: string, systemId: string) =>
    api.delete(`/organizations/${orgId}/systems/${systemId}`),

  setDecider: (orgId: string, systemId: string, executor: ExecutorUnit) =>
    api.post<AgentSystem>(`/organizations/${orgId}/systems/${systemId}/decider`, executor).then(res => res.data),

  addActor: (orgId: string, systemId: string, executor: ExecutorUnit) =>
    api.post<AgentSystem>(`/organizations/${orgId}/systems/${systemId}/actors`, executor).then(res => res.data),

  removeActor: (orgId: string, systemId: string, actorIdx: number) =>
    api.delete(`/organizations/${orgId}/systems/${systemId}/actors/${actorIdx}`),

  setFeedbacker: (orgId: string, systemId: string, executor: ExecutorUnit) =>
    api.post<AgentSystem>(`/organizations/${orgId}/systems/${systemId}/feedbacker`, executor).then(res => res.data),

  start: (orgId: string, systemId: string) =>
    api.post<AgentSystem>(`/organizations/${orgId}/systems/${systemId}/start`).then(res => res.data),

  stop: (orgId: string, systemId: string) =>
    api.post<AgentSystem>(`/organizations/${orgId}/systems/${systemId}/stop`).then(res => res.data),

  executeLoop: (orgId: string, systemId: string) =>
    api.post<SystemLoopStep>(`/organizations/${orgId}/systems/${systemId}/loop`).then(res => res.data),

  getSteps: (orgId: string, systemId: string) =>
    api.get<SystemLoopStep[]>(`/organizations/${orgId}/systems/${systemId}/steps`).then(res => res.data),

  getAvailableExecutors: (orgId: string) =>
    api.get<AvailableExecutors>(`/organizations/${orgId}/available-executors`).then(res => res.data),
};

export const generatorApi = {
  generate: (req: GenerateRequest) =>
    api.post<GenerateResponse>('/generator/generate', req).then(res => res.data),
};
