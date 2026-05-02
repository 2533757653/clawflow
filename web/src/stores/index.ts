import { create } from 'zustand';
import type {
  Organization,
  Role,
  Task,
  DataFlow,
  Knowledge,
  Skill
} from '../types';
import {
  organizationApi,
  roleApi,
  taskApi,
  dataflowApi,
  knowledgeApi,
  skillApi,
  ragApi,
} from '../services/api';
import type { RAGStats, SearchResult } from '../types';

interface AppState {
  organizations: Organization[];
  currentOrganizationId: string | null;
  roles: Role[];
  tasks: Task[];
  dataflows: DataFlow[];
  knowledge: Knowledge[];
  skills: Skill[];
  clawhubSkills: Skill[];
  ragStats: RAGStats | null;
  semanticSearchResults: SearchResult[];

  loading: {
    organizations: boolean;
    roles: boolean;
    tasks: boolean;
    dataflows: boolean;
    knowledge: boolean;
    skills: boolean;
    rag: boolean;
  };

  setCurrentOrganization: (orgId: string | null) => void;

  loadOrganizations: () => Promise<void>;
  createOrganization: (org: Partial<Organization>) => Promise<Organization>;
  updateOrganization: (id: string, org: Partial<Organization>) => Promise<void>;
  deleteOrganization: (id: string) => Promise<void>;
  deployOrganization: (id: string) => Promise<void>;
  startOrganization: (id: string) => Promise<void>;
  stopOrganization: (id: string) => Promise<void>;

  loadRoles: () => Promise<void>;
  createRole: (role: Partial<Role>) => Promise<Role>;
  updateRole: (roleId: string, role: Partial<Role>) => Promise<void>;
  deleteRole: (roleId: string) => Promise<void>;

  loadTasks: (orgId: string) => Promise<void>;
  createTask: (orgId: string, task: Partial<Task>) => Promise<Task>;
  updateTask: (orgId: string, taskId: string, task: Partial<Task>) => Promise<void>;
  deleteTask: (orgId: string, taskId: string) => Promise<void>;

  loadDataflows: (orgId: string) => Promise<void>;
  createDataflow: (orgId: string, dataflow: Partial<DataFlow>) => Promise<DataFlow>;
  updateDataflow: (orgId: string, dataflowId: string, dataflow: Partial<DataFlow>) => Promise<void>;
  deleteDataflow: (orgId: string, dataflowId: string) => Promise<void>;

  loadKnowledge: (orgId: string) => Promise<void>;
  createKnowledge: (orgId: string, knowledge: Partial<Knowledge>) => Promise<Knowledge>;
  updateKnowledge: (orgId: string, knowledgeId: string, knowledge: Partial<Knowledge>) => Promise<void>;
  deleteKnowledge: (orgId: string, knowledgeId: string) => Promise<void>;

  loadSkills: () => Promise<void>;
  searchClawhubSkills: (q?: string, tag?: string) => Promise<void>;
  installSkill: (skillId: string) => Promise<void>;
  uninstallSkill: (skillId: string) => Promise<void>;
  installSkillToRole: (skillId: string, roleId: string) => Promise<void>;

  loadRagStats: () => Promise<void>;
  semanticSearch: (query: string, orgId: string, topK?: number) => Promise<SearchResult[]>;
  reindexKnowledgeBase: (orgId: string) => Promise<{ knowledge_count: number; total_chunks: number }>;
}

export const useStore = create<AppState>((set, get) => ({
  organizations: [],
  currentOrganizationId: null,
  roles: [],
  tasks: [],
  dataflows: [],
  knowledge: [],
  skills: [],
  clawhubSkills: [],
  ragStats: null,
  semanticSearchResults: [],

  loading: {
    organizations: false,
    roles: false,
    tasks: false,
    dataflows: false,
    knowledge: false,
    skills: false,
    rag: false,
  },

  setCurrentOrganization: (orgId) => {
    set({
      currentOrganizationId: orgId,
      tasks: [],
      dataflows: [],
      knowledge: [],
    });

    if (orgId) {
      get().loadTasks(orgId);
      get().loadDataflows(orgId);
      get().loadKnowledge(orgId);
    }
  },

  loadOrganizations: async () => {
    set((state) => ({ ...state, loading: { ...state.loading, organizations: true } }));
    try {
      const data = await organizationApi.list();
      set((state) => ({ ...state, organizations: data, loading: { ...state.loading, organizations: false } }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, organizations: false } }));
    }
  },

  createOrganization: async (org) => {
    const created = await organizationApi.create(org);
    set((state) => ({ ...state, organizations: [...state.organizations, created] }));
    return created;
  },

  updateOrganization: async (id, org) => {
    const updated = await organizationApi.update(id, org);
    set((state) => ({
      ...state,
      organizations: state.organizations.map((o) => (o.id === id ? updated : o))
    }));
  },

  deleteOrganization: async (id) => {
    await organizationApi.delete(id);
    set((state) => ({
      ...state,
      organizations: state.organizations.filter((o) => o.id !== id),
      currentOrganizationId: state.currentOrganizationId === id ? null : state.currentOrganizationId
    }));
  },

  deployOrganization: async (id) => {
    await organizationApi.deploy(id);
    await get().loadOrganizations();
  },

  startOrganization: async (id) => {
    await organizationApi.start(id);
    await get().loadOrganizations();
  },

  stopOrganization: async (id) => {
    await organizationApi.stop(id);
    await get().loadOrganizations();
  },

  loadRoles: async () => {
    set((state) => ({ ...state, loading: { ...state.loading, roles: true } }));
    try {
      const data = await roleApi.list();
      set((state) => ({ ...state, roles: data, loading: { ...state.loading, roles: false } }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, roles: false } }));
    }
  },

  createRole: async (role) => {
    const created = await roleApi.create(role);
    set((state) => ({ ...state, roles: [...state.roles, created] }));
    return created;
  },

  updateRole: async (roleId, role) => {
    const updated = await roleApi.update(roleId, role);
    set((state) => ({
      ...state,
      roles: state.roles.map((r) => (r.id === roleId ? updated : r))
    }));
  },

  deleteRole: async (roleId) => {
    await roleApi.delete(roleId);
    set((state) => ({
      ...state,
      roles: state.roles.filter((r) => r.id !== roleId)
    }));
  },

  loadTasks: async (orgId) => {
    set((state) => ({ ...state, loading: { ...state.loading, tasks: true } }));
    try {
      const data = await taskApi.list(orgId);
      set((state) => ({
        ...state,
        ...(state.currentOrganizationId === orgId ? { tasks: data } : {}),
        loading: { ...state.loading, tasks: false }
      }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, tasks: false } }));
    }
  },

  createTask: async (orgId, task) => {
    const created = await taskApi.create(orgId, task);
    set((state) => ({ ...state, tasks: [...state.tasks, created] }));
    return created;
  },

  updateTask: async (orgId, taskId, task) => {
    const updated = await taskApi.update(orgId, taskId, task);
    set((state) => ({
      ...state,
      tasks: state.tasks.map((t) => (t.id === taskId ? updated : t))
    }));
  },

  deleteTask: async (orgId, taskId) => {
    await taskApi.delete(orgId, taskId);
    set((state) => ({
      ...state,
      tasks: state.tasks.filter((t) => t.id !== taskId)
    }));
  },

  loadDataflows: async (orgId) => {
    set((state) => ({ ...state, loading: { ...state.loading, dataflows: true } }));
    try {
      const data = await dataflowApi.list(orgId);
      set((state) => ({
        ...state,
        ...(state.currentOrganizationId === orgId ? { dataflows: data } : {}),
        loading: { ...state.loading, dataflows: false }
      }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, dataflows: false } }));
    }
  },

  createDataflow: async (orgId, dataflow) => {
    const created = await dataflowApi.create(orgId, dataflow);
    set((state) => ({ ...state, dataflows: [...state.dataflows, created] }));
    return created;
  },

  updateDataflow: async (orgId, dataflowId, dataflow) => {
    const updated = await dataflowApi.update(orgId, dataflowId, dataflow);
    set((state) => ({
      ...state,
      dataflows: state.dataflows.map((d) => (d.id === dataflowId ? updated : d))
    }));
  },

  deleteDataflow: async (orgId, dataflowId) => {
    await dataflowApi.delete(orgId, dataflowId);
    set((state) => ({
      ...state,
      dataflows: state.dataflows.filter((d) => d.id !== dataflowId)
    }));
  },

  loadKnowledge: async (orgId) => {
    set((state) => ({ ...state, loading: { ...state.loading, knowledge: true } }));
    try {
      const data = await knowledgeApi.list(orgId);
      set((state) => ({
        ...state,
        ...(state.currentOrganizationId === orgId ? { knowledge: data } : {}),
        loading: { ...state.loading, knowledge: false }
      }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, knowledge: false } }));
    }
  },

  createKnowledge: async (orgId, knowledge) => {
    const created = await knowledgeApi.create(orgId, knowledge);
    set((state) => ({ ...state, knowledge: [...state.knowledge, created] }));
    return created;
  },

  updateKnowledge: async (orgId, knowledgeId, knowledge) => {
    const updated = await knowledgeApi.update(orgId, knowledgeId, knowledge);
    set((state) => ({
      ...state,
      knowledge: state.knowledge.map((k) => (k.id === knowledgeId ? updated : k))
    }));
  },

  deleteKnowledge: async (orgId, knowledgeId) => {
    await knowledgeApi.delete(orgId, knowledgeId);
    set((state) => ({
      ...state,
      knowledge: state.knowledge.filter((k) => k.id !== knowledgeId)
    }));
  },

  loadSkills: async () => {
    set((state) => ({ ...state, loading: { ...state.loading, skills: true } }));
    try {
      const [installed, clawhub] = await Promise.all([
        skillApi.listInstalled(),
        skillApi.search()
      ]);
      set((state) => ({
        ...state,
        skills: installed,
        clawhubSkills: clawhub,
        loading: { ...state.loading, skills: false }
      }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, skills: false } }));
    }
  },

  searchClawhubSkills: async (q, tag) => {
    const data = await skillApi.search(q, tag);
    set((state) => ({ ...state, clawhubSkills: data }));
  },

  installSkill: async (skillId) => {
    await skillApi.install(skillId);
    await get().loadSkills();
  },

  uninstallSkill: async (skillId) => {
    await skillApi.uninstall(skillId);
    await get().loadSkills();
  },

  installSkillToRole: async (skillId, roleId) => {
    await skillApi.installToRole(skillId, roleId);
    await get().loadSkills();
  },

  loadRagStats: async () => {
    set((state) => ({ ...state, loading: { ...state.loading, rag: true } }));
    try {
      const stats = await ragApi.getStats();
      set((state) => ({ ...state, ragStats: stats, loading: { ...state.loading, rag: false } }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, rag: false } }));
    }
  },

  semanticSearch: async (query, orgId, topK = 5) => {
    set((state) => ({ ...state, loading: { ...state.loading, rag: true } }));
    try {
      const response = await ragApi.query({
        query,
        top_k: topK,
        organization_id: orgId,
        doc_types: ['knowledge']
      });
      const results: SearchResult[] = response.results.map(r => ({
        id: r.chunk_id,
        content: r.content,
        score: r.score,
        source: (r.metadata?.title as string) || 'Unknown'
      }));
      set((state) => ({ ...state, semanticSearchResults: results, loading: { ...state.loading, rag: false } }));
      return results;
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, rag: false } }));
      return [];
    }
  },

  reindexKnowledgeBase: async (orgId) => {
    set((state) => ({ ...state, loading: { ...state.loading, rag: true } }));
    try {
      const result = await ragApi.indexKnowledgeBase(orgId);
      await get().loadRagStats();
      return result;
    } finally {
      set((state) => ({ ...state, loading: { ...state.loading, rag: false } }));
    }
  },
}));
