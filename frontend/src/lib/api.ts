import axios from 'axios';

const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  created_at: string;
}

export interface Rule {
  id: number;
  dataset_id: number;
  rule_type: string;
  params: Record<string, unknown>;
  threshold: number;
  severity: string;
  enabled: boolean;
  created_at: string;
}

export interface Incident {
  id: number;
  dataset_id: number;
  rule_id: number;
  created_at: string;
  metric_value: number;
  passed: boolean;
  severity: string;
  description: string;
  acknowledged: boolean;
}

export async function fetchDatasets(): Promise<Dataset[]> {
  const res = await axios.get(`${backendUrl}/datasets`);
  return res.data;
}

export async function fetchIncidents(params: Record<string, unknown> = {}): Promise<Incident[]> {
  const res = await axios.get(`${backendUrl}/incidents`, { params });
  return res.data;
}

export async function acknowledgeIncident(id: number, comment: string | null = null): Promise<Incident> {
  const res = await axios.post(`${backendUrl}/incidents/${id}/acknowledge`, {
    comment,
  });
  return res.data;
}

export async function fetchRules(datasetId?: number): Promise<Rule[]> {
  const params = datasetId ? { dataset_id: datasetId } : {};
  const res = await axios.get(`${backendUrl}/rules`, { params });
  return res.data;
}

export interface CreateRuleInput {
  dataset_id: number;
  rule_type: string;
  params: Record<string, unknown>;
  threshold: number;
  severity: string;
  enabled: boolean;
}

export async function createRule(input: CreateRuleInput): Promise<Rule> {
  const res = await axios.post(`${backendUrl}/rules`, input);
  return res.data;
}