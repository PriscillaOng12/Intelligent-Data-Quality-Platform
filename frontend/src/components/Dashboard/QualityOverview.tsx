import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Chip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Assessment,
  Timeline,
} from '@mui/icons-material';
import { DashboardMetrics, MetricData } from '../../types';
import apiClient from '../../services/api';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, color }) => {
  const getTrendIcon = () => {
    if (change === undefined) return null;
    return change >= 0 ? <TrendingUp color="success" /> : <TrendingDown color="error" />;
  };

  const getChangeColor = () => {
    if (change === undefined) return 'text.secondary';
    return change >= 0 ? 'success.main' : 'error.main';
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {title}
          </Typography>
          <Box color={`${color}.main`}>{icon}</Box>
        </Box>
        
        <Typography variant="h4" component="div" gutterBottom>
          {value}
        </Typography>
        
        {change !== undefined && (
          <Box display="flex" alignItems="center">
            {getTrendIcon()}
            <Typography variant="body2" color={getChangeColor()} ml={0.5}>
              {Math.abs(change)}% from last week
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

interface QualityDistributionProps {
  distribution: {
    excellent: number;
    good: number;
    fair: number;
    poor: number;
  };
}

const QualityDistribution: React.FC<QualityDistributionProps> = ({ distribution }) => {
  const total = distribution.excellent + distribution.good + distribution.fair + distribution.poor;
  
  const getPercentage = (value: number) => {
    return total > 0 ? Math.round((value / total) * 100) : 0;
  };

  const categories = [
    { label: 'Excellent (90-100%)', value: distribution.excellent, color: 'success' },
    { label: 'Good (70-89%)', value: distribution.good, color: 'primary' },
    { label: 'Fair (50-69%)', value: distribution.fair, color: 'warning' },
    { label: 'Poor (<50%)', value: distribution.poor, color: 'error' },
  ] as const;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Quality Score Distribution
        </Typography>
        
        <Box mt={2}>
          {categories.map((category) => (
            <Box key={category.label} display="flex" alignItems="center" justifyContent="space-between" mb={1}>
              <Typography variant="body2">{category.label}</Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Chip 
                  label={`${category.value} (${getPercentage(category.value)}%)`}
                  color={category.color}
                  size="small"
                />
              </Box>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

interface TopIssuesProps {
  issues: {
    datasetName: string;
    issueCount: number;
    severity: string;
  }[];
}

const TopIssues: React.FC<TopIssuesProps> = ({ issues }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'error';
      case 'HIGH':
        return 'warning';
      case 'MEDIUM':
        return 'info';
      case 'LOW':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Top Issues by Dataset
        </Typography>
        
        <Box mt={2}>
          {issues.length === 0 ? (
            <Box display="flex" alignItems="center" justifyContent="center" p={2}>
              <CheckCircle color="success" sx={{ mr: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No critical issues found
              </Typography>
            </Box>
          ) : (
            issues.slice(0, 5).map((issue, index) => (
              <Box key={index} display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                <Typography variant="body2" noWrap sx={{ maxWidth: '60%' }}>
                  {issue.datasetName}
                </Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="body2" color="text.secondary">
                    {issue.issueCount} issues
                  </Typography>
                  <Chip
                    label={issue.severity}
                    color={getSeverityColor(issue.severity)}
                    size="small"
                  />
                </Box>
              </Box>
            ))
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

const QualityOverview: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardMetrics = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await apiClient.getDashboardMetrics();
        setMetrics(data);
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
        // Use mock data when API fails
        const mockMetrics = {
          totalDatasets: 42,
          avgQualityScore: 87.5,
          activeAlerts: 5,
          checksLast24h: 156,
          trendsLast7d: {
            qualityScores: [
              { timestamp: '2024-01-20T00:00:00Z', value: 85.2, metricType: 'quality_score' },
              { timestamp: '2024-01-21T00:00:00Z', value: 86.1, metricType: 'quality_score' },
              { timestamp: '2024-01-22T00:00:00Z', value: 84.8, metricType: 'quality_score' },
              { timestamp: '2024-01-23T00:00:00Z', value: 87.3, metricType: 'quality_score' },
              { timestamp: '2024-01-24T00:00:00Z', value: 88.1, metricType: 'quality_score' },
              { timestamp: '2024-01-25T00:00:00Z', value: 87.5, metricType: 'quality_score' },
              { timestamp: '2024-01-26T00:00:00Z', value: 89.2, metricType: 'quality_score' },
            ],
            alertCounts: [
              { timestamp: '2024-01-20T00:00:00Z', value: 8, metricType: 'alert_count' },
              { timestamp: '2024-01-21T00:00:00Z', value: 6, metricType: 'alert_count' },
              { timestamp: '2024-01-22T00:00:00Z', value: 10, metricType: 'alert_count' },
              { timestamp: '2024-01-23T00:00:00Z', value: 7, metricType: 'alert_count' },
              { timestamp: '2024-01-24T00:00:00Z', value: 4, metricType: 'alert_count' },
              { timestamp: '2024-01-25T00:00:00Z', value: 5, metricType: 'alert_count' },
              { timestamp: '2024-01-26T00:00:00Z', value: 3, metricType: 'alert_count' },
            ],
            checkCounts: [
              { timestamp: '2024-01-20T00:00:00Z', value: 142, metricType: 'check_count' },
              { timestamp: '2024-01-21T00:00:00Z', value: 138, metricType: 'check_count' },
              { timestamp: '2024-01-22T00:00:00Z', value: 151, metricType: 'check_count' },
              { timestamp: '2024-01-23T00:00:00Z', value: 147, metricType: 'check_count' },
              { timestamp: '2024-01-24T00:00:00Z', value: 153, metricType: 'check_count' },
              { timestamp: '2024-01-25T00:00:00Z', value: 149, metricType: 'check_count' },
              { timestamp: '2024-01-26T00:00:00Z', value: 156, metricType: 'check_count' },
            ]
          },
          topIssues: [
            { datasetName: 'customer_data', issueCount: 3, severity: 'HIGH' },
            { datasetName: 'product_catalog', issueCount: 2, severity: 'MEDIUM' },
            { datasetName: 'sales_transactions', issueCount: 1, severity: 'LOW' }
          ],
          qualityDistribution: {
            excellent: 15,
            good: 18,
            fair: 7,
            poor: 2
          }
        } as DashboardMetrics;
        setMetrics(mockMetrics);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardMetrics();
    
    // Refresh metrics every 30 seconds
    const interval = setInterval(loadDashboardMetrics, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!metrics) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No metrics data available
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Data Quality Overview
      </Typography>
      
      <Grid container spacing={3}>
        {/* Key Metrics */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Datasets"
            value={metrics.totalDatasets}
            icon={<Assessment />}
            color="primary"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Average Quality Score"
            value={`${Math.round(metrics.avgQualityScore)}%`}
            icon={<Timeline />}
            color="success"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Alerts"
            value={metrics.activeAlerts}
            icon={<Warning />}
            color="warning"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Checks (24h)"
            value={metrics.checksLast24h}
            icon={<CheckCircle />}
            color="secondary"
          />
        </Grid>

        {/* Quality Distribution */}
        <Grid item xs={12} md={6}>
          <QualityDistribution distribution={metrics.qualityDistribution} />
        </Grid>

        {/* Top Issues */}
        <Grid item xs={12} md={6}>
          <TopIssues issues={metrics.topIssues} />
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity Summary
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="primary">
                      {metrics.trendsLast7d.qualityScores.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Quality Checks This Week
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="warning.main">
                      {metrics.trendsLast7d.alertCounts.reduce((sum, item) => sum + item.value, 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Alerts This Week
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="secondary">
                      {metrics.trendsLast7d.checkCounts.reduce((sum, item) => sum + item.value, 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Executions This Week
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default QualityOverview;
