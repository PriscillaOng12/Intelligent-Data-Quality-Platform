import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert as MuiAlert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Grid,
  Tooltip,
  Badge,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Warning,
  Error,
  Info,
  CheckCircle,
  Refresh,
  Visibility,
  Assignment,
  Done,
  Close,
  Schedule,
  NotificationsActive,
  FilterList,
} from '@mui/icons-material';
import { Alert } from '../../types';
import apiClient from '../../services/api';

interface AlertCardProps {
  alert: Alert;
  onViewDetails: (alert: Alert) => void;
  onAcknowledge: (alertId: string) => void;
  onResolve: (alertId: string) => void;
}

const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onViewDetails,
  onAcknowledge,
  onResolve,
}) => {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <Error color="error" />;
      case 'HIGH':
        return <Warning color="warning" />;
      case 'MEDIUM':
        return <Info color="info" />;
      case 'LOW':
        return <CheckCircle color="success" />;
      default:
        return <Info color="action" />;
    }
  };

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN':
        return 'error';
      case 'ACKNOWLEDGED':
        return 'warning';
      case 'RESOLVED':
        return 'success';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
          <Box display="flex" alignItems="center">
            {getSeverityIcon(alert.severity)}
            <Typography variant="h6" sx={{ ml: 1 }}>
              {alert.title}
            </Typography>
          </Box>
          <Box display="flex" gap={1}>
            <Chip
              label={alert.severity}
              color={getSeverityColor(alert.severity) as any}
              size="small"
            />
            <Chip
              label={alert.status}
              color={getStatusColor(alert.status) as any}
              size="small"
            />
          </Box>
        </Box>

        <Typography variant="body2" color="text.secondary" paragraph>
          {alert.message}
        </Typography>

        <Grid container spacing={2} mb={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="caption" color="text.secondary">
              Dataset: {alert.datasetName || 'N/A'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="caption" color="text.secondary">
              Created: {formatTimestamp(alert.createdAt)}
            </Typography>
          </Grid>
        </Grid>

        <Box display="flex" justifyContent="flex-end" gap={1}>
          <Button
            size="small"
            startIcon={<Visibility />}
            onClick={() => onViewDetails(alert)}
          >
            Details
          </Button>
          
          {alert.status === 'OPEN' && (
            <Button
              size="small"
              color="warning"
              startIcon={<Assignment />}
              onClick={() => onAcknowledge(alert.id)}
            >
              Acknowledge
            </Button>
          )}
          
          {alert.status !== 'RESOLVED' && (
            <Button
              size="small"
              color="success"
              startIcon={<Done />}
              onClick={() => onResolve(alert.id)}
            >
              Resolve
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

interface AlertDetailsDialogProps {
  alert: Alert | null;
  open: boolean;
  onClose: () => void;
  onAcknowledge: (alertId: string) => void;
  onResolve: (alertId: string, resolution?: string) => void;
}

const AlertDetailsDialog: React.FC<AlertDetailsDialogProps> = ({
  alert,
  open,
  onClose,
  onAcknowledge,
  onResolve,
}) => {
  const [resolution, setResolution] = useState('');
  const [showResolutionInput, setShowResolutionInput] = useState(false);

  const handleResolve = () => {
    if (alert) {
      onResolve(alert.id, resolution);
      setResolution('');
      setShowResolutionInput(false);
      onClose();
    }
  };

  const handleAcknowledge = () => {
    if (alert) {
      onAcknowledge(alert.id);
      onClose();
    }
  };

  if (!alert) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Alert Details</Typography>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Box display="flex" alignItems="center" mb={2}>
              {alert.severity === 'CRITICAL' && <Error color="error" />}
              {alert.severity === 'HIGH' && <Warning color="warning" />}
              {alert.severity === 'MEDIUM' && <Info color="info" />}
              {alert.severity === 'LOW' && <CheckCircle color="success" />}
              <Typography variant="h5" sx={{ ml: 1 }}>
                {alert.title}
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="primary">Severity</Typography>
            <Chip label={alert.severity} color="error" size="small" />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="primary">Status</Typography>
            <Chip label={alert.status} color="warning" size="small" />
          </Grid>
          
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="primary">Message</Typography>
            <Typography variant="body1">{alert.message}</Typography>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="primary">Dataset</Typography>
            <Typography variant="body2">{alert.datasetName || 'N/A'}</Typography>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="primary">Source</Typography>
            <Typography variant="body2">{alert.datasetName || 'N/A'}</Typography>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="primary">Created</Typography>
            <Typography variant="body2">
              {new Date(alert.createdAt).toLocaleString()}
            </Typography>
          </Grid>
          
          {alert.acknowledgedAt && (
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="primary">Acknowledged</Typography>
              <Typography variant="body2">
                {new Date(alert.acknowledgedAt).toLocaleString()}
              </Typography>
            </Grid>
          )}
          
          {alert.resolvedAt && (
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="primary">Resolved</Typography>
              <Typography variant="body2">
                {new Date(alert.resolvedAt).toLocaleString()}
              </Typography>
            </Grid>
          )}
          
          {alert.resolvedAt && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="primary">Resolution</Typography>
              <Typography variant="body2">{`Resolved at ${alert.resolvedAt}`}</Typography>
            </Grid>
          )}
          
          {alert.metadata && Object.keys(alert.metadata).length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="primary">Additional Information</Typography>
              <Paper sx={{ p: 1, backgroundColor: 'grey.50' }}>
                {Object.entries(alert.metadata).map(([key, value]) => (
                  <Box key={key} display="flex" justifyContent="space-between" mb={0.5}>
                    <Typography variant="caption">{key}:</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {String(value)}
                    </Typography>
                  </Box>
                ))}
              </Paper>
            </Grid>
          )}
          
          {showResolutionInput && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Resolution Notes"
                multiline
                rows={3}
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
                placeholder="Enter resolution details..."
              />
            </Grid>
          )}
        </Grid>
      </DialogContent>
      
      <DialogActions>
        {alert.status === 'OPEN' && (
          <Button
            color="warning"
            startIcon={<Assignment />}
            onClick={handleAcknowledge}
          >
            Acknowledge
          </Button>
        )}
        
        {alert.status !== 'RESOLVED' && (
          <>
            {!showResolutionInput ? (
              <Button
                color="success"
                startIcon={<Done />}
                onClick={() => setShowResolutionInput(true)}
              >
                Resolve
              </Button>
            ) : (
              <Button
                color="success"
                startIcon={<Done />}
                onClick={handleResolve}
              >
                Confirm Resolution
              </Button>
            )}
          </>
        )}
        
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

const AlertCenter: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  
  // Filters
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      if (severityFilter) params.severity = severityFilter;
      
      const response = await apiClient.getAlerts(params);
      setAlerts(response.data || []);
    } catch (error) {
      console.error('Failed to load alerts:', error);
      // Use mock data when API fails
      const mockAlerts = [
        {
          id: '1',
          title: 'Data Quality Check Failed',
          message: 'Customer dataset failed completeness check with 15% null values in email field',
          severity: 'HIGH' as const,
          status: 'OPEN' as const,
          datasetId: 'dataset-1',
          datasetName: 'customer_data',
          createdAt: new Date().toISOString(),
        },
        {
          id: '2',
          title: 'Schema Drift Detected',
          message: 'Product table schema has changed - new column "category_v2" detected',
          severity: 'MEDIUM' as const,
          status: 'ACKNOWLEDGED' as const,
          datasetId: 'dataset-2',
          datasetName: 'product_catalog',
          createdAt: new Date(Date.now() - 3600000).toISOString(),
          acknowledgedAt: new Date(Date.now() - 1800000).toISOString(),
        },
        {
          id: '3',
          title: 'Data Freshness Alert',
          message: 'Sales data is 6 hours old, exceeding freshness threshold',
          severity: 'LOW' as const,
          status: 'RESOLVED' as const,
          datasetId: 'dataset-3',
          datasetName: 'sales_transactions',
          createdAt: new Date(Date.now() - 7200000).toISOString(),
          acknowledgedAt: new Date(Date.now() - 3600000).toISOString(),
          resolvedAt: new Date(Date.now() - 1800000).toISOString()
        }
      ];
      setAlerts(mockAlerts);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, severityFilter]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  // Auto-refresh alerts every 30 seconds
  useEffect(() => {
    const interval = setInterval(loadAlerts, 30000);
    return () => clearInterval(interval);
  }, [loadAlerts]);

  const handleViewDetails = (alert: Alert) => {
    setSelectedAlert(alert);
    setDetailsOpen(true);
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await apiClient.acknowledgeAlert(alertId);
      await loadAlerts(); // Refresh the list
    } catch (err: unknown) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolve = async (alertId: string, resolution?: string) => {
    try {
      await apiClient.resolveAlert(alertId, resolution);
      await loadAlerts(); // Refresh the list
    } catch (err: unknown) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const handleSeverityFilterChange = (event: SelectChangeEvent<string>) => {
    setSeverityFilter(event.target.value);
  };

  const handleStatusFilterChange = (event: SelectChangeEvent<string>) => {
    setStatusFilter(event.target.value);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    // Set status filter based on tab
    switch (newValue) {
      case 0: // All alerts
        setStatusFilter('');
        break;
      case 1: // Active alerts
        setStatusFilter('OPEN');
        break;
      case 2: // Acknowledged alerts
        setStatusFilter('ACKNOWLEDGED');
        break;
      case 3: // Resolved alerts
        setStatusFilter('RESOLVED');
        break;
    }
  };

  // Filter alerts based on current tab
  const filteredAlerts = alerts.filter(alert => {
    if (activeTab === 1) return alert.status === 'OPEN';
    if (activeTab === 2) return alert.status === 'ACKNOWLEDGED';
    if (activeTab === 3) return alert.status === 'RESOLVED';
    return true; // All alerts
  });

  const activeAlertsCount = alerts.filter(a => a.status === 'OPEN').length;
  const acknowledgedAlertsCount = alerts.filter(a => a.status === 'ACKNOWLEDGED').length;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Alert Center</Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Badge badgeContent={activeAlertsCount} color="error">
            <NotificationsActive />
          </Badge>
          <IconButton onClick={loadAlerts} disabled={loading}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Alert Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="error.main">
                    {activeAlertsCount}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Alerts
                  </Typography>
                </Box>
                <Warning color="error" fontSize="large" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="warning.main">
                    {acknowledgedAlertsCount}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Acknowledged
                  </Typography>
                </Box>
                <Assignment color="warning" fontSize="large" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="success.main">
                    {alerts.filter(a => a.status === 'RESOLVED').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Resolved
                  </Typography>
                </Box>
                <CheckCircle color="success" fontSize="large" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="primary.main">
                    {alerts.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Alerts
                  </Typography>
                </Box>
                <NotificationsActive color="primary" fontSize="large" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Severity</InputLabel>
              <Select
                value={severityFilter}
                onChange={handleSeverityFilterChange}
                label="Severity"
              >
                <MenuItem value="">All Severities</MenuItem>
                <MenuItem value="CRITICAL">Critical</MenuItem>
                <MenuItem value="HIGH">High</MenuItem>
                <MenuItem value="MEDIUM">Medium</MenuItem>
                <MenuItem value="LOW">Low</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Alert Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label={`All (${alerts.length})`} />
          <Tab 
            label={
              <Badge badgeContent={activeAlertsCount} color="error">
                Active
              </Badge>
            } 
          />
          <Tab label={`Acknowledged (${acknowledgedAlertsCount})`} />
          <Tab label={`Resolved (${alerts.filter(a => a.status === 'RESOLVED').length})`} />
        </Tabs>
      </Paper>

      {error && (
        <MuiAlert severity="error" sx={{ mb: 2 }}>
          {error}
        </MuiAlert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {filteredAlerts.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="text.secondary">
                No alerts found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {activeTab === 0 && 'No alerts have been generated yet'}
                {activeTab === 1 && 'No active alerts at this time'}
                {activeTab === 2 && 'No acknowledged alerts'}
                {activeTab === 3 && 'No resolved alerts'}
              </Typography>
            </Box>
          ) : (
            <Box>
              {filteredAlerts.map((alert) => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  onViewDetails={handleViewDetails}
                  onAcknowledge={handleAcknowledge}
                  onResolve={handleResolve}
                />
              ))}
            </Box>
          )}
        </>
      )}

      <AlertDetailsDialog
        alert={selectedAlert}
        open={detailsOpen}
        onClose={() => {
          setDetailsOpen(false);
          setSelectedAlert(null);
        }}
        onAcknowledge={handleAcknowledge}
        onResolve={handleResolve}
      />
    </Box>
  );
};

export default AlertCenter;
