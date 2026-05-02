import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
});

export interface SuggestResponsibilitiesResponse {
  responsibilities: string[];
  confidence: number;
}

export interface GenerateSoulResponse {
  soul_template: string;
}

export interface SuggestDivisionResponse {
  suggested_division?: string;
  alternatives: string[];
}

export const roleSuggestionApi = {
  suggestResponsibilities: (request: {
    name: string;
    description?: string;
    division?: string;
    hierarchy_level: number;
  }) => api.post<SuggestResponsibilitiesResponse>('/roles/suggest-responsibilities', request),

  generateSoul: (request: {
    name: string;
    description?: string;
    division?: string;
    responsibilities: string[];
  }) => api.post<GenerateSoulResponse>('/roles/generate-soul', request),

  suggestDivision: (request: {
    name: string;
    description: string;
  }) => api.post<SuggestDivisionResponse>('/roles/suggest-division', request),

  applySuggestions: (request: {
    role_id: string;
    responsibilities?: string[];
    soul_template?: string;
  }) => api.post('/roles/apply-suggestions', request),
};