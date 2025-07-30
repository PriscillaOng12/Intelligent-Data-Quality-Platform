import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Pagination,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore,
  Visibility,
  Assessment,
  Schedule,
  Storage,
  TableChart,
  FilterList,
  Refresh,
} from '@mui/icons-material';
import { Dataset, DatasetFilter, PaginatedResponse } from '../../types';
import apiClient from '../../services/api';

interface DatasetCardProps {
  dataset: Dataset;
  onViewDetails: (datasetId: string) => void;
}

const DatasetCard: React.FC<DatasetCardProps> = ({ dataset, onViewDetails }) => {
  const getQualityColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    if (score >= 50) return 'info';
    return 'error';
  };

  const formatLastUpdated = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString();
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
          <Typography variant="h6" noWrap sx={{ maxWidth: '80%' }}>
            {dataset.name}
          </Typography>
          <Chip
            label={`${dataset.qualityScore ?? 0}%`}
            color={getQualityColor(dataset.qualityScore ?? 0)}
            size="small"
          />
        </Box>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          {dataset.description || 'No description available'}
        </Typography>
        
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <Storage fontSize="small" color="primary" />
          <Typography variant="body2">
            Source: {dataset.source || 'Unknown'}
          </Typography>
        </Box>
        
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <TableChart fontSize="small" color="primary" />
          <Typography variant="body2">
            Rows: {dataset.rowCount?.toLocaleString() || 'N/A'}
          </Typography>
        </Box>
        
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <Schedule fontSize="small" color="primary" />
          <Typography variant="body2">
            Updated: {formatLastUpdated(dataset.updatedAt)}
          </Typography>
        </Box>
        
        <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
          {dataset.tags.slice(0, 3).map((tag) => (
            <Chip key={tag} label={tag} size="small" variant="outlined" />
          ))}
          {dataset.tags.length > 3 && (
            <Chip label={`+${dataset.tags.length - 3} more`} size="small" variant="outlined" />
          )}
        </Box>
      </CardContent>
      
      <Box p={2} pt={0}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<Visibility />}
          onClick={() => onViewDetails(dataset.id)}
        >
          View Details
        </Button>
      </Box>
    </Card>
  );
};

interface DatasetDetailsProps {
  dataset: Dataset;
}

const DatasetDetails: React.FC<DatasetDetailsProps> = ({ dataset }) => {
  const columns = dataset.schema || [];
  const checks = dataset.qualityChecks || [];

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {dataset.name}
      </Typography>
      
      <Grid container spacing={3}>
        {/* Basic Information */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box mb={2}>
              <Typography variant="subtitle2" color="primary">Description</Typography>
              <Typography variant="body2">
                {dataset.description || 'No description available'}
              </Typography>
            </Box>
            
            <Box mb={2}>
              <Typography variant="subtitle2" color="primary">Source</Typography>
              <Typography variant="body2">{dataset.source || 'Unknown'}</Typography>
            </Box>
            
            <Box mb={2}>
              <Typography variant="subtitle2" color="primary">Row Count</Typography>
              <Typography variant="body2">
                {dataset.rowCount?.toLocaleString() || 'N/A'}
              </Typography>
            </Box>
            
            <Box mb={2}>
              <Typography variant="subtitle2" color="primary">Last Updated</Typography>
              <Typography variant="body2">
                {new Date(dataset.updatedAt).toLocaleString()}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="subtitle2" color="primary">Tags</Typography>
              <Box display="flex" gap={1} flexWrap="wrap" mt={1}>
                {dataset.tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" />
                ))}
              </Box>
            </Box>
          </Paper>
        </Grid>
        
        {/* Quality Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quality Metrics
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box display="flex" justifyContent="center" mb={3}>
              <Box textAlign="center">
                <Typography variant="h3" color="primary">
                  {dataset.qualityScore}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Overall Quality Score
                </Typography>
              </Box>
            </Box>
            
            {checks.length > 0 && (
              <Box>
                <Typography variant="subtitle2" color="primary" mb={1}>
                  Recent Quality Checks
                </Typography>
                {checks.slice(0, 3).map((check, index) => (
                  <Box key={index} display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">{`Check ${index + 1} (${check.rules.length} rules)`}</Typography>
                    <Chip
                      label={check.isActive ? 'Active' : 'Inactive'}
                      color={check.isActive ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* Schema Information */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6">Schema ({columns.length} columns)</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Column Name</TableCell>
                      <TableCell>Data Type</TableCell>
                      <TableCell>Nullable</TableCell>
                      <TableCell>Description</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {columns.map((column) => (
                      <TableRow key={column.name}>
                        <TableCell>{column.name}</TableCell>
                        <TableCell>{column.type}</TableCell>
                        <TableCell>{column.nullable ? 'Yes' : 'No'}</TableCell>
                        <TableCell>{column.description || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        </Grid>
      </Grid>
    </Box>
  );
};

const DatasetBrowser: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [qualityFilter, setQualityFilter] = useState('');
  const [availableSources, setAvailableSources] = useState<string[]>([]);

  const loadDatasets = useCallback(async (page: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const filters: DatasetFilter = {
        search: searchTerm || undefined,
        owner: sourceFilter || undefined,
        qualityScoreRange: qualityFilter ? { 
          min: parseInt(qualityFilter), 
          max: 100 
        } : undefined,
      };
      
      const response = await apiClient.getDatasets(filters, page, 12);
      setDatasets(response.items);
      setTotalPages(response.totalPages);
      setCurrentPage(response.currentPage);
      
      // Extract unique sources for filter dropdown
      const sources = [...new Set(response.items.map(d => d.source).filter(Boolean))];
      setAvailableSources(sources as string[]);
      
    } catch (err) {
      console.error('Failed to load datasets:', err);
      // Use mock data when API fails
      const mockDatasets = [
        {
          id: 'dataset-1',
          name: 'customer_data',
          description: 'Customer information including demographics and contact details',
          source: 'PostgreSQL',
          schema: [],
          qualityScore: 92.5,
          rowCount: 125000,
          columns: 18,
          size: 45000000,
          tags: ['PII', 'Customer', 'Production'],
          owner: 'data-team@company.com',
          createdAt: '2024-01-15T08:30:00Z',
          updatedAt: '2024-01-26T14:22:00Z',
          lastModified: '2024-01-26T14:22:00Z',
          status: 'active' as const,
          location: 'postgres://db/public/customers',
          format: 'table'
        },
        {
          id: 'dataset-2',
          name: 'product_catalog',
          description: 'Complete product catalog with pricing and inventory information',
          source: 'MongoDB',
          schema: [],
          qualityScore: 87.2,
          rowCount: 85000,
          columns: 25,
          size: 32000000,
          tags: ['Product', 'Inventory', 'E-commerce'],
          owner: 'product-team@company.com',
          createdAt: '2024-01-10T09:15:00Z',
          updatedAt: '2024-01-26T12:10:00Z',
          lastModified: '2024-01-26T12:10:00Z',
          status: 'active' as const,
          location: 'mongodb://cluster/ecommerce/products',
          format: 'collection'
        },
        {
          id: 'dataset-3',
          name: 'sales_transactions',
          description: 'Daily sales transaction records from all channels',
          source: 'BigQuery',
          schema: [],
          qualityScore: 94.8,
          rowCount: 2500000,
          columns: 15,
          size: 180000000,
          tags: ['Sales', 'Transactions', 'Analytics'],
          owner: 'analytics-team@company.com',
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-26T15:00:00Z',
          lastModified: '2024-01-26T15:00:00Z',
          status: 'active' as const,
          location: 'bigquery://project/analytics/transactions',
          format: 'table'
        }
      ] as Dataset[];
      setDatasets(mockDatasets);
      setTotalPages(1);
      setCurrentPage(1);
      setAvailableSources(['PostgreSQL', 'MongoDB', 'BigQuery']);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, sourceFilter, qualityFilter]);

  useEffect(() => {
    loadDatasets(1);
  }, [loadDatasets]);

  const handleSearch = () => {
    loadDatasets(1);
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    loadDatasets(page);
  };

  const handleSourceFilterChange = (event: SelectChangeEvent<string>) => {
    setSourceFilter(event.target.value);
  };

  const handleQualityFilterChange = (event: SelectChangeEvent<string>) => {
    setQualityFilter(event.target.value);
  };

  const handleViewDetails = async (datasetId: string) => {
    try {
      const dataset = await apiClient.getDataset(datasetId);
      setSelectedDataset(dataset);
    } catch (err) {
      console.error('Failed to load dataset details:', err);
    }
  };

  const handleBack = () => {
    setSelectedDataset(null);
  };

  if (selectedDataset) {
    return (
      <Box>
        <Button onClick={handleBack} sx={{ mb: 2 }}>
          ← Back to Catalog
        </Button>
        <DatasetDetails dataset={selectedDataset} />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Data Catalog</Typography>
        <IconButton onClick={() => loadDatasets(currentPage)}>
          <Refresh />
        </IconButton>
      </Box>
      
      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search datasets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Source</InputLabel>
              <Select
                value={sourceFilter}
                onChange={handleSourceFilterChange}
                label="Source"
              >
                <MenuItem value="">All Sources</MenuItem>
                {availableSources.map((source) => (
                  <MenuItem key={source} value={source}>
                    {source}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Quality</InputLabel>
              <Select
                value={qualityFilter}
                onChange={handleQualityFilterChange}
                label="Quality"
              >
                <MenuItem value="">All Quality Scores</MenuItem>
                <MenuItem value="90">Excellent (90%+)</MenuItem>
                <MenuItem value="70">Good (70%+)</MenuItem>
                <MenuItem value="50">Fair (50%+)</MenuItem>
                <MenuItem value="0">All</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="contained"
              onClick={handleSearch}
              startIcon={<FilterList />}
            >
              Filter
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Grid container spacing={3}>
            {datasets.map((dataset) => (
              <Grid item xs={12} sm={6} md={4} key={dataset.id}>
                <DatasetCard dataset={dataset} onViewDetails={handleViewDetails} />
              </Grid>
            ))}
          </Grid>

          {datasets.length === 0 && !loading && (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="text.secondary">
                No datasets found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try adjusting your search criteria
              </Typography>
            </Box>
          )}

          {totalPages > 1 && (
            <Box display="flex" justifyContent="center" mt={4}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default DatasetBrowser;
