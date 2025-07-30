// Core Entities
export interface Dataset {
  id: string;
  name: string;
  description?: string;
  source: string;
  schema: SchemaField[];
  createdAt: string;
  updatedAt: string;
  lastModified: string;
  size: number;
  rowCount: number;
  columns: number;
  qualityScore?: number;
  status: 'active' | 'inactive' | 'archived';
  tags: string[];
  owner: string;
  location: string;
  format: string;
  partitions?: string[];
  qualityChecks?: QualityCheck[];
  metadata?: Record<string, any>;
}

export interface SchemaField {
  name: string;
  type: string;
  nullable: boolean;
  description?: string;
  constraints?: string[];
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'user' | 'viewer';
  permissions: string[];
  createdAt: string;
  lastLogin?: string;
}

export interface QualityCheck {
  id: string;
  datasetId: string;
  rules: QualityRule[];
  schedule?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  lastRun?: string;
  nextRun?: string;
}

export interface QualityRule {
  id: string;
  ruleType: 'null_check' | 'uniqueness_check' | 'range_check' | 'pattern_check' | 'custom';
  column: string;
  threshold: number;
  parameters?: Record<string, any>;
  description?: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface QualityResult {
  id: string;
  checkId: string;
  executionTime: string;
  status: 'running' | 'completed' | 'failed';
  overallScore: number;
  ruleResults: RuleResult[];
  executionDuration: number;
  recordsProcessed: number;
  anomaliesDetected?: Anomaly[];
  summary: {
    passed: number;
    failed: number;
    warnings: number;
  };
}

export interface RuleResult {
  ruleId: string;
  passed: boolean;
  score: number;
  actualValue: number;
  threshold: number;
  message: string;
  details?: Record<string, any>;
}

export interface Anomaly {
  id: string;
  timestamp: string;
  anomalyScore: number;
  feature: string;
  actualValue: any;
  expectedValue: any;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  rowIndices?: number[];
}

export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'CLOSED';
  datasetId: string;
  datasetName?: string;
  ruleId?: string;
  createdAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  assigneeId?: string;
  assigneeName?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface LineageNode {
  id: string;
  name: string;
  type: 'table' | 'view' | 'file' | 'stream' | 'api';
  nodeType: 'source' | 'transformation' | 'sink';
  datasetId?: string;
  qualityScore?: number;
  lastUpdated?: string;
  description?: string;
  owner?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  position?: {
    x: number;
    y: number;
  };
}

export interface LineageEdge {
  id: string;
  sourceId: string;
  targetId: string;
  type: 'data_flow' | 'transformation' | 'dependency';
  transformationType?: string;
  description?: string;
  createdAt: string;
}

export interface MetricData {
  timestamp: string;
  value: number;
  datasetId?: string;
  metricType: string;
}

export interface DashboardMetrics {
  totalDatasets: number;
  avgQualityScore: number;
  activeAlerts: number;
  checksLast24h: number;
  trendsLast7d: {
    qualityScores: MetricData[];
    alertCounts: MetricData[];
    checkCounts: MetricData[];
  };
  topIssues: {
    datasetName: string;
    issueCount: number;
    severity: string;
  }[];
  qualityDistribution: {
    excellent: number;
    good: number;
    fair: number;
    poor: number;
  };
}

// Base Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  totalItems: number;
  totalPages: number;
  currentPage: number;
  pageSize: number;
}

export interface DatasetFilter {
  search?: string;
  owner?: string;
  tags?: string[];
  status?: string[];
  qualityScoreRange?: {
    min: number;
    max: number;
  };
  createdAfter?: string;
  createdBefore?: string;
}

export interface AlertFilter {
  severity?: string[];
  status?: string[];
  datasetId?: string;
  assigneeId?: string;
  tags?: string[];
  createdAfter?: string;
  createdBefore?: string;
}

export interface QualityScoreRange {
  min: number;
  max: number;
}

export interface DateRange {
  start: string;
  end: string;
}

export interface LineageGraph {
  nodes: LineageNode[];
  edges: LineageEdge[];
  metadata?: {
    depth: number;
    direction: 'upstream' | 'downstream' | 'both';
    includeMetrics: boolean;
  };
}

export interface Report {
  id: string;
  name: string;
  description?: string;
  type: 'quality_summary' | 'lineage_analysis' | 'alert_summary' | 'custom';
  config: ReportConfig;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  schedule?: string;
  lastGenerated?: string;
  format: 'pdf' | 'html' | 'csv' | 'json';
}

export interface ReportConfig {
  timeRange: string;
  datasets?: string[];
  includeCharts: boolean;
  includeDetails: boolean;
  customSections?: ReportSection[];
}

export interface ReportSection {
  type: string;
  title: string;
  config: Record<string, any>;
}

export interface PaginationParams {
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  filters?: Record<string, any>;
}

export interface FilterOptions {
  datasets?: string[];
  severity?: string[];
  status?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  qualityScoreRange?: {
    min: number;
    max: number;
  };
}

// ML and Analytics Types
export interface MLModel {
  id: string;
  name: string;
  type: 'anomaly_detection' | 'quality_prediction' | 'data_drift';
  version: string;
  status: 'training' | 'deployed' | 'inactive';
  accuracy?: number;
  createdAt: string;
  updatedAt: string;
  config: Record<string, any>;
}

export interface DataDriftResult {
  id: string;
  datasetId: string;
  referenceDate: string;
  currentDate: string;
  driftScore: number;
  isDriftDetected: boolean;
  features: {
    name: string;
    driftScore: number;
    pValue: number;
    isDrifted: boolean;
  }[];
  createdAt: string;
}

// Component Props Types
export interface TableColumn {
  field: string;
  headerName: string;
  width?: number;
  flex?: number;
  sortable?: boolean;
  filterable?: boolean;
  renderCell?: (params: any) => React.ReactNode;
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'scatter' | 'heatmap';
  title?: string;
  xAxis?: string;
  yAxis?: string;
  data: any[];
  options?: Record<string, any>;
}

export interface NotificationSettings {
  id: string;
  userId: string;
  emailEnabled: boolean;
  slackEnabled: boolean;
  webhookUrl?: string;
  alertThresholds: {
    quality: number;
    performance: number;
    availability: number;
  };
  channels: string[];
  createdAt: string;
  updatedAt: string;
}

export interface IntegrationConfig {
  id: string;
  name: string;
  type: 'databricks' | 'snowflake' | 'bigquery' | 'redshift' | 's3' | 'kafka';
  config: Record<string, any>;
  isActive: boolean;
  lastSync?: string;
  createdAt: string;
  updatedAt: string;
}

// Export commonly used type unions
export type QualitySeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'CLOSED';
export type DatasetStatus = 'active' | 'inactive' | 'archived';
export type UserRole = 'admin' | 'user' | 'viewer';
export type NodeType = 'source' | 'transformation' | 'sink';
export type EdgeType = 'data_flow' | 'transformation' | 'dependency';
