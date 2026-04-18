import { create } from 'zustand';
import type {
  Organization,
  Role,
  Task,
  DataFlow,
  Knowledge,
  Skill,
  AgentSystem,
  SystemLoopStep,
  ExecutorUnit,
  AvailableExecutors
} from '../types';
import {
  organizationApi,
  roleApi,
  taskApi,
  dataflowApi,
  knowledgeApi,
  skillApi,
  systemApi
} from '../services/api';

interface AppState {
  organizations: Organization[];
  currentOrganizationId: string | null;
  roles: Role[];
  tasks: Task[];
  dataflows: DataFlow[];
  knowledge: Knowledge[];
  skills: Skill[];
  clawhubSkills: Skill[];
  systems: AgentSystem[];
  systemSteps: SystemLoopStep[];
  availableExecutors: AvailableExecutors;

  loading: {
    organizations: boolean;
    roles: boolean;
    tasks: boolean;
    dataflows: boolean;
    knowledge: boolean;
    skills: boolean;
    systems: boolean;
  };

  setCurrentOrganization: (orgId: string | null) => void;

  loadOrganizations: () => Promise<void>;
  createOrganization: (org: Partial<Organization>) => Promise<Organization>;
  updateOrganization: (id: string, org: Partial<Organization>) => Promise<void>;
  deleteOrganization: (id: string) => Promise<void>;
  deployOrganization: (id: string) => Promise<void>;

  loadRoles: (orgId: string) => Promise<void>;
  createRole: (orgId: string, role: Partial<Role>) => Promise<Role>;
  updateRole: (orgId: string, roleId: string, role: Partial<Role>) => Promise<void>;
  deleteRole: (orgId: string, roleId: string) => Promise<void>;

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

  loadSystems: (orgId: string) => Promise<void>;
  createSystem: (orgId: string, system: Partial<AgentSystem>) => Promise<AgentSystem>;
  updateSystem: (orgId: string, systemId: string, system: Partial<AgentSystem>) => Promise<void>;
  deleteSystem: (orgId: string, systemId: string) => Promise<void>;
  setSystemDecider: (orgId: string, systemId: string, executor: ExecutorUnit) => Promise<void>;
  addSystemActor: (orgId: string, systemId: string, executor: ExecutorUnit) => Promise<void>;
  removeSystemActor: (orgId: string, systemId: string, actorIdx: number) => Promise<void>;
  setSystemFeedbacker: (orgId: string, systemId: string, executor: ExecutorUnit) => Promise<void>;
  startSystem: (orgId: string, systemId: string) => Promise<void>;
  stopSystem: (orgId: string, systemId: string) => Promise<void>;
  executeSystemLoop: (orgId: string, systemId: string) => Promise<void>;
  loadSystemSteps: (orgId: string, systemId: string) => Promise<void>;
  loadAvailableExecutors: (orgId: string) => Promise<void>;
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
  systems: [],
  systemSteps: [],
  availableExecutors: { roles: [], systems: [] },

  loading: {
    organizations: false,
    roles: false,
    tasks: false,
    dataflows: false,
    knowledge: false,
    skills: false,
    systems: false,
  },

  setCurrentOrganization: (orgId) => {
    set({ currentOrganizationId: orgId });
    if (orgId) {
      get().loadRoles(orgId);
      get().loadTasks(orgId);
      get().loadDataflows(orgId);
      get().loadKnowledge(orgId);
      get().loadSystems(orgId);
      get().loadAvailableExecutors(orgId);
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

  loadRoles: async (orgId) => {
    set((state) => ({ ...state, loading: { ...state.loading, roles: true } }));
    try {
      const data = await roleApi.list(orgId);
      set((state) => ({ ...state, roles: data, loading: { ...state.loading, roles: false } }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, roles: false } }));
    }
  },

  createRole: async (orgId, role) => {
    const created = await roleApi.create(orgId, role);
    set((state) => ({ ...state, roles: [...state.roles, created] }));
    return created;
  },

  updateRole: async (orgId, roleId, role) => {
    const updated = await roleApi.update(orgId, roleId, role);
    set((state) => ({
      ...state,
      roles: state.roles.map((r) => (r.id === roleId ? updated : r))
    }));
  },

  deleteRole: async (orgId, roleId) => {
    await roleApi.delete(orgId, roleId);
    set((state) => ({
      ...state,
      roles: state.roles.filter((r) => r.id !== roleId)
    }));
  },

  loadTasks: async (orgId) => {
    set((state) => ({ ...state, loading: { ...state.loading, tasks: true } }));
    try {
      const data = await taskApi.list(orgId);
      set((state) => ({ ...state, tasks: data, loading: { ...state.loading, tasks: false } }));
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
      set((state) => ({ ...state, dataflows: data, loading: { ...state.loading, dataflows: false } }));
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
      set((state) => ({ ...state, knowledge: data, loading: { ...state.loading, knowledge: false } }));
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

  loadSystems: async (orgId) => {
    set((state) => ({ ...state, loading: { ...state.loading, systems: true } }));
    try {
      const data = await systemApi.list(orgId);
      set((state) => ({ ...state, systems: data, loading: { ...state.loading, systems: false } }));
    } catch {
      set((state) => ({ ...state, loading: { ...state.loading, systems: false } }));
    }
  },

  createSystem: async (orgId, system) => {
    const created = await systemApi.create(orgId, system);
    set((state) => ({ ...state, systems: [...state.systems, created] }));
    return created;
  },

  updateSystem: async (orgId, systemId, system) => {
    const updated = await systemApi.update(orgId, systemId, system);
    set((state) => ({
      ...state,
      systems: state.systems.map((s) => (s.id === systemId ? updated : s))
    }));
  },

  deleteSystem: async (orgId, systemId) => {
    await systemApi.delete(orgId, systemId);
    set((state) => ({
      ...state,
      systems: state.systems.filter((s) => s.id !== systemId)
    }));
  },

  setSystemDecider: async (orgId, systemId, executor) => {
    await systemApi.setDecider(orgId, systemId, executor);
    await get().loadSystems(orgId);
  },

  addSystemActor: async (orgId, systemId, executor) => {
    await systemApi.addActor(orgId, systemId, executor);
    await get().loadSystems(orgId);
  },

  removeSystemActor: async (orgId, systemId, actorIdx) => {
    await systemApi.removeActor(orgId, systemId, actorIdx);
    await get().loadSystems(orgId);
  },

  setSystemFeedbacker: async (orgId, systemId, executor) => {
    await systemApi.setFeedbacker(orgId, systemId, executor);
    await get().loadSystems(orgId);
  },

  startSystem: async (orgId, systemId) => {
    await systemApi.start(orgId, systemId);
    await get().loadSystems(orgId);
  },

  stopSystem: async (orgId, systemId) => {
    await systemApi.stop(orgId, systemId);
    await get().loadSystems(orgId);
  },

  executeSystemLoop: async (orgId, systemId) => {
    await systemApi.executeLoop(orgId, systemId);
    await get().loadSystemSteps(orgId, systemId);
    await get().loadSystems(orgId);
  },

  loadSystemSteps: async (orgId, systemId) => {
    const data = await systemApi.getSteps(orgId, systemId);
    set((state) => ({ ...state, systemSteps: data }));
  },

  loadAvailableExecutors: async (orgId) => {
    const data = await systemApi.getAvailableExecutors(orgId);
    set((state) => ({ ...state, availableExecutors: data }));
  },
}));
