import axios from 'axios';

export interface ExecuteRequest {
  input_data: Record<string, unknown>;
  dataflow_id?: string;
  input_role_id?: string;
}

export interface NodeResult {
  node_id: string;
  role_id?: string;
  task_id?: string;
  output: Record<string, unknown>;
  error?: string;
  execution_time_ms: number;
}

export interface ExecutionResult {
  execution_id: string;
  status: 'completed' | 'failed' | 'partial';
  node_results: NodeResult[];
  final_output: Record<string, unknown>;
}

const api = axios.create({
  baseURL: '/api/v1',
});

export const executionApi = {
  execute: (orgId: string, request: ExecuteRequest) =>
    api.post<ExecutionResult>(`/organizations/${orgId}/execute`, request).then(res => res.data),

  getExecutionStatus: (orgId: string, executionId: string) =>
    api.get(`/organizations/${orgId}/execution/${executionId}`).then(res => res.data),

  validateDataflow: (orgId: string, dataflowId: string) =>
    api.get(`/organizations/${orgId}/dataflows/${dataflowId}/validate`).then(res => res.data),
};