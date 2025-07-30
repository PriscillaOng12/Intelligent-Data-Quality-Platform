import { 
  Dataset, 
  QualityCheck, 
  QualityResult, 
  Alert, 
  LineageNode, 
  LineageEdge, 
  DashboardMetrics, 
  ApiResponse, 
  PaginationParams,
  DatasetFilter,
  PaginatedResponse 
} from '../types';

const API_BASE_URL = 'http://localhost:8001/api/v1';

class ApiClient {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('accessToken');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      headers: this.getAuthHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // Dashboard APIs
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await this.request<DashboardMetrics>('/dashboard/metrics');
    return response.data;
  }

  // Dataset APIs
  async getDatasets(
    filters?: DatasetFilter, 
    page: number = 1, 
    pageSize: number = 20
  ): Promise<PaginatedResponse<Dataset>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: pageSize.toString(),
    });

    if (filters) {
      if (filters.search) params.append('search', filters.search);
      if (filters.owner) params.append('owner', filters.owner);
      if (filters.qualityScoreRange) {
        params.append('quality_min', filters.qualityScoreRange.min.toString());
        params.append('quality_max', filters.qualityScoreRange.max.toString());
      }
      if (filters.tags) {
        filters.tags.forEach(tag => params.append('tags', tag));
      }
    }

    const response = await this.request<{
      items: Dataset[];
      total: number;
      page: number;
      pages: number;
      size: number;
    }>(`/datasets?${params}`);
    
    return {
      items: response.data.items,
      totalItems: response.data.total,
      totalPages: response.data.pages,
      currentPage: response.data.page,
      pageSize: response.data.size,
    };
  }

  async getDataset(id: string): Promise<Dataset> {
    const response = await this.request<Dataset>(`/datasets/${id}`);
    return response.data;
  }

  async createDataset(dataset: Omit<Dataset, 'id' | 'createdAt' | 'updatedAt'>): Promise<Dataset> {
    const response = await this.request<Dataset>('/datasets', {
      method: 'POST',
      body: JSON.stringify(dataset),
    });
    return response.data;
  }

  async updateDataset(id: string, dataset: Partial<Dataset>): Promise<Dataset> {
    const response = await this.request<Dataset>(`/datasets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dataset),
    });
    return response.data;
  }

  async deleteDataset(id: string): Promise<void> {
    await this.request(`/datasets/${id}`, {
      method: 'DELETE',
    });
  }

  // Quality Check APIs
  async getQualityChecks(datasetId?: string): Promise<QualityCheck[]> {
    const endpoint = datasetId ? `/quality/checks?dataset_id=${datasetId}` : '/quality/checks';
    const response = await this.request<QualityCheck[]>(endpoint);
    return response.data;
  }

  async getQualityCheck(id: string): Promise<QualityCheck> {
    const response = await this.request<QualityCheck>(`/quality/checks/${id}`);
    return response.data;
  }

  async createQualityCheck(check: Omit<QualityCheck, 'id' | 'createdAt' | 'updatedAt'>): Promise<QualityCheck> {
    const response = await this.request<QualityCheck>('/quality/checks', {
      method: 'POST',
      body: JSON.stringify(check),
    });
    return response.data;
  }

  async updateQualityCheck(id: string, check: Partial<QualityCheck>): Promise<QualityCheck> {
    const response = await this.request<QualityCheck>(`/quality/checks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(check),
    });
    return response.data;
  }

  async deleteQualityCheck(id: string): Promise<void> {
    await this.request(`/quality/checks/${id}`, {
      method: 'DELETE',
    });
  }

  async runQualityCheck(datasetId: string): Promise<{ checkId: string }> {
    const response = await this.request<{ checkId: string }>(`/quality/check/${datasetId}`, {
      method: 'POST',
    });
    return response.data;
  }

  // Quality Results APIs
  async getQualityResults(checkId?: string, datasetId?: string): Promise<QualityResult[]> {
    let endpoint = '/quality/results';
    const params = new URLSearchParams();
    
    if (checkId) params.append('check_id', checkId);
    if (datasetId) params.append('dataset_id', datasetId);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }

    const response = await this.request<QualityResult[]>(endpoint);
    return response.data;
  }

  async getQualityResult(id: string): Promise<QualityResult> {
    const response = await this.request<QualityResult>(`/quality/results/${id}`);
    return response.data;
  }

  async getQualityMetrics(datasetId: string, timeRange?: string): Promise<any> {
    let endpoint = `/quality/metrics/${datasetId}`;
    if (timeRange) {
      endpoint += `?time_range=${timeRange}`;
    }
    const response = await this.request<any>(endpoint);
    return response.data;
  }

  // Alert APIs
  async getAlerts(params?: PaginationParams & { 
    status?: string; 
    severity?: string; 
    datasetId?: string; 
  }): Promise<ApiResponse<Alert[]>> {
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    return this.request<Alert[]>(`/alerts${queryString ? `?${queryString}` : ''}`);
  }

  async getAlert(id: string): Promise<Alert> {
    const response = await this.request<Alert>(`/alerts/${id}`);
    return response.data;
  }

  async createAlert(alert: Omit<Alert, 'id' | 'createdAt'>): Promise<Alert> {
    const response = await this.request<Alert>('/alerts', {
      method: 'POST',
      body: JSON.stringify(alert),
    });
    return response.data;
  }

  async updateAlert(id: string, alert: Partial<Alert>): Promise<Alert> {
    const response = await this.request<Alert>(`/alerts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(alert),
    });
    return response.data;
  }

  async acknowledgeAlert(id: string): Promise<Alert> {
    const response = await this.request<Alert>(`/alerts/${id}/acknowledge`, {
      method: 'POST',
    });
    return response.data;
  }

  async resolveAlert(id: string, resolution?: string): Promise<Alert> {
    const response = await this.request<Alert>(`/alerts/${id}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution }),
    });
    return response.data;
  }

  // Lineage APIs
  async getLineageNodes(datasetId?: string): Promise<LineageNode[]> {
    const endpoint = datasetId ? `/lineage/nodes?dataset_id=${datasetId}` : '/lineage/nodes';
    const response = await this.request<LineageNode[]>(endpoint);
    return response.data;
  }

  async getLineageEdges(nodeId?: string): Promise<LineageEdge[]> {
    const endpoint = nodeId ? `/lineage/edges?node_id=${nodeId}` : '/lineage/edges';
    const response = await this.request<LineageEdge[]>(endpoint);
    return response.data;
  }

  async getUpstreamLineage(datasetId: string): Promise<{ nodes: LineageNode[]; edges: LineageEdge[] }> {
    const response = await this.request<{ nodes: LineageNode[]; edges: LineageEdge[] }>(
      `/lineage/upstream/${datasetId}`
    );
    return response.data;
  }

  async getDownstreamLineage(datasetId: string): Promise<{ nodes: LineageNode[]; edges: LineageEdge[] }> {
    const response = await this.request<{ nodes: LineageNode[]; edges: LineageEdge[] }>(
      `/lineage/downstream/${datasetId}`
    );
    return response.data;
  }

  async getFullLineage(datasetId: string): Promise<{ nodes: LineageNode[]; edges: LineageEdge[] }> {
    const response = await this.request<{ nodes: LineageNode[]; edges: LineageEdge[] }>(
      `/lineage/full/${datasetId}`
    );
    return response.data;
  }

  // Authentication APIs
  async login(email: string, password: string): Promise<{ 
    accessToken: string; 
    refreshToken: string; 
    user: any; 
  }> {
    const response = await this.request<{ 
      accessToken: string; 
      refreshToken: string; 
      user: any; 
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    return response.data;
  }

  async refreshToken(refreshToken: string): Promise<{ 
    accessToken: string; 
    refreshToken: string; 
  }> {
    const response = await this.request<{ 
      accessToken: string; 
      refreshToken: string; 
    }>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refreshToken }),
    });
    return response.data;
  }

  async getCurrentUser(): Promise<any> {
    const response = await this.request<any>('/auth/me');
    return response.data;
  }

  async logout(): Promise<void> {
    await this.request('/auth/logout', {
      method: 'POST',
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
