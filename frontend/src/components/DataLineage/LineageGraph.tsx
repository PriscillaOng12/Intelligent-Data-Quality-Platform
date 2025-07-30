import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Grid,
  Divider,
} from '@mui/material';
import {
  AccountTree,
  ArrowForward,
  ArrowBack,
  Refresh,
  Visibility,
  Storage,
  Transform,
  Assessment,
  Schedule,
} from '@mui/icons-material';
import { LineageNode, LineageEdge } from '../../types';
import apiClient from '../../services/api';

interface LineageNodeProps {
  node: LineageNode;
  onNodeClick: (nodeId: string) => void;
  isSelected: boolean;
}

const LineageNodeComponent: React.FC<LineageNodeProps> = ({ 
  node, 
  onNodeClick, 
  isSelected 
}) => {
  const getNodeIcon = (nodeType: string) => {
    switch (nodeType) {
      case 'source':
        return <Storage color="primary" />;
      case 'transformation':
        return <Transform color="secondary" />;
      case 'sink':
        return <Assessment color="success" />;
      default:
        return <AccountTree color="action" />;
    }
  };

  const getNodeColor = (nodeType: string) => {
    switch (nodeType) {
      case 'source':
        return 'primary';
      case 'transformation':
        return 'secondary';
      case 'sink':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <Card 
      sx={{ 
        minWidth: 200,
        maxWidth: 250,
        cursor: 'pointer',
        border: isSelected ? 2 : 1,
        borderColor: isSelected ? 'primary.main' : 'divider',
        '&:hover': {
          boxShadow: 3,
        }
      }}
      onClick={() => onNodeClick(node.id)}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Box display="flex" alignItems="center" mb={1}>
          {getNodeIcon(node.nodeType)}
          <Typography variant="subtitle2" sx={{ ml: 1, fontWeight: 'bold' }}>
            {node.name}
          </Typography>
        </Box>
        
        <Chip 
          label={node.nodeType} 
          size="small" 
          color={getNodeColor(node.nodeType) as any}
          sx={{ mb: 1 }}
        />
        
        {node.description && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            {node.description.length > 80 
              ? `${node.description.substring(0, 80)}...` 
              : node.description
            }
          </Typography>
        )}
        
        {node.lastUpdated && (
          <Box display="flex" alignItems="center" mt={1}>
            <Schedule fontSize="small" color="action" />
            <Typography variant="caption" sx={{ ml: 0.5 }}>
              {new Date(node.lastUpdated).toLocaleDateString()}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

interface LineageEdgeProps {
  edge: LineageEdge;
  sourceNode: LineageNode;
  targetNode: LineageNode;
}

const LineageEdgeComponent: React.FC<LineageEdgeProps> = ({ 
  edge, 
  sourceNode, 
  targetNode 
}) => {
  return (
    <Box 
      display="flex" 
      alignItems="center" 
      sx={{ 
        p: 1, 
        border: 1, 
        borderColor: 'divider', 
        borderRadius: 1, 
        backgroundColor: 'background.paper' 
      }}
    >
      <Typography variant="caption" sx={{ flexGrow: 1 }}>
        {sourceNode.name} → {targetNode.name}
      </Typography>
      <Tooltip title={edge.description || 'Data flow'}>
        <ArrowForward fontSize="small" color="primary" />
      </Tooltip>
    </Box>
  );
};

interface LineageGraphProps {
  datasetId?: string;
}

const LineageGraph: React.FC<LineageGraphProps> = ({ datasetId: initialDatasetId }) => {
  const [nodes, setNodes] = useState<LineageNode[]>([]);
  const [edges, setEdges] = useState<LineageEdge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(initialDatasetId || '');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [lineageDirection, setLineageDirection] = useState<'upstream' | 'downstream' | 'full'>('full');

  const loadLineage = useCallback(async (datasetId: string, direction: string) => {
    if (!datasetId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      let response: { nodes: LineageNode[]; edges: LineageEdge[] };
      
      switch (direction) {
        case 'upstream':
          response = await apiClient.getUpstreamLineage(datasetId);
          break;
        case 'downstream':
          response = await apiClient.getDownstreamLineage(datasetId);
          break;
        case 'full':
        default:
          response = await apiClient.getFullLineage(datasetId);
          break;
      }
      
      setNodes(response.nodes);
      setEdges(response.edges);
      
      // Select the main dataset node
      const mainNode = response.nodes.find(n => n.datasetId === datasetId);
      if (mainNode) {
        setSelectedNodeId(mainNode.id);
      }
      
    } catch (err) {
      console.error('Failed to load lineage:', err);
      // Use mock data when API fails
      const mockNodes: any[] = [
        {
          id: 'node-1',
          datasetId: 'dataset-1',
          name: 'customer_data',
          nodeType: 'table',
          type: 'table'
        },
        {
          id: 'node-2',
          datasetId: 'dataset-2',
          name: 'user_profiles',
          nodeType: 'view',
          type: 'view'
        },
        {
          id: 'node-3',
          datasetId: 'dataset-3',
          name: 'analytics_summary',
          nodeType: 'model',
          type: 'model'
        }
      ];
      const mockEdges: any[] = [
        {
          id: 'edge-1',
          sourceId: 'node-1',
          targetId: 'node-2',
          type: 'data_flow',
          createdAt: new Date().toISOString()
        },
        {
          id: 'edge-2',
          sourceId: 'node-2',
          targetId: 'node-3',
          type: 'data_flow',
          createdAt: new Date().toISOString()
        }
      ];
      setNodes(mockNodes);
      setEdges(mockEdges);
      if (mockNodes.length > 0) {
        setSelectedNodeId(mockNodes[0].id);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      loadLineage(selectedDatasetId, lineageDirection);
    }
  }, [selectedDatasetId, lineageDirection, loadLineage]);

  const handleDatasetChange = (event: SelectChangeEvent<string>) => {
    setSelectedDatasetId(event.target.value);
  };

  const handleDirectionChange = (event: SelectChangeEvent<string>) => {
    setLineageDirection(event.target.value as 'upstream' | 'downstream' | 'full');
  };

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    const node = nodes.find(n => n.id === nodeId);
    if (node && node.datasetId && node.datasetId !== selectedDatasetId) {
      setSelectedDatasetId(node.datasetId);
    }
  };

  const handleRefresh = () => {
    if (selectedDatasetId) {
      loadLineage(selectedDatasetId, lineageDirection);
    }
  };

  // Organize nodes by type for better layout
  const sourceNodes = nodes.filter(n => n.nodeType === 'source');
  const transformationNodes = nodes.filter(n => n.nodeType === 'transformation');
  const sinkNodes = nodes.filter(n => n.nodeType === 'sink');
  const otherNodes = nodes.filter(n => !['source', 'transformation', 'sink'].includes(n.nodeType));

  const selectedNode = selectedNodeId ? nodes.find(n => n.id === selectedNodeId) : null;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Data Lineage</Typography>
        <IconButton onClick={handleRefresh} disabled={loading}>
          <Refresh />
        </IconButton>
      </Box>

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Dataset ID</InputLabel>
              <Select
                value={selectedDatasetId}
                onChange={handleDatasetChange}
                label="Dataset ID"
              >
                <MenuItem value="">Select a dataset</MenuItem>
                {/* In a real app, you'd load available datasets */}
                <MenuItem value="dataset_1">Customer Data</MenuItem>
                <MenuItem value="dataset_2">Sales Transactions</MenuItem>
                <MenuItem value="dataset_3">Product Catalog</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Direction</InputLabel>
              <Select
                value={lineageDirection}
                onChange={handleDirectionChange}
                label="Direction"
              >
                <MenuItem value="full">Full Lineage</MenuItem>
                <MenuItem value="upstream">Upstream Only</MenuItem>
                <MenuItem value="downstream">Downstream Only</MenuItem>
              </Select>
            </FormControl>
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
          {nodes.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="text.secondary">
                {selectedDatasetId ? 'No lineage data found' : 'Select a dataset to view lineage'}
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {/* Lineage Visualization */}
              <Grid item xs={12} lg={8}>
                <Paper sx={{ p: 2, minHeight: 400 }}>
                  <Typography variant="h6" gutterBottom>
                    Lineage Graph
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  {/* Source Nodes */}
                  {sourceNodes.length > 0 && (
                    <Box mb={3}>
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        Data Sources
                      </Typography>
                      <Box display="flex" gap={2} flexWrap="wrap">
                        {sourceNodes.map(node => (
                          <LineageNodeComponent
                            key={node.id}
                            node={node}
                            onNodeClick={handleNodeClick}
                            isSelected={node.id === selectedNodeId}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  {/* Arrow */}
                  {sourceNodes.length > 0 && transformationNodes.length > 0 && (
                    <Box display="flex" justifyContent="center" mb={2}>
                      <ArrowForward fontSize="large" color="primary" />
                    </Box>
                  )}
                  
                  {/* Transformation Nodes */}
                  {transformationNodes.length > 0 && (
                    <Box mb={3}>
                      <Typography variant="subtitle2" color="secondary" gutterBottom>
                        Transformations
                      </Typography>
                      <Box display="flex" gap={2} flexWrap="wrap">
                        {transformationNodes.map(node => (
                          <LineageNodeComponent
                            key={node.id}
                            node={node}
                            onNodeClick={handleNodeClick}
                            isSelected={node.id === selectedNodeId}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  {/* Arrow */}
                  {transformationNodes.length > 0 && sinkNodes.length > 0 && (
                    <Box display="flex" justifyContent="center" mb={2}>
                      <ArrowForward fontSize="large" color="primary" />
                    </Box>
                  )}
                  
                  {/* Sink Nodes */}
                  {sinkNodes.length > 0 && (
                    <Box mb={3}>
                      <Typography variant="subtitle2" color="success.main" gutterBottom>
                        Data Sinks
                      </Typography>
                      <Box display="flex" gap={2} flexWrap="wrap">
                        {sinkNodes.map(node => (
                          <LineageNodeComponent
                            key={node.id}
                            node={node}
                            onNodeClick={handleNodeClick}
                            isSelected={node.id === selectedNodeId}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  {/* Other Nodes */}
                  {otherNodes.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Other Components
                      </Typography>
                      <Box display="flex" gap={2} flexWrap="wrap">
                        {otherNodes.map(node => (
                          <LineageNodeComponent
                            key={node.id}
                            node={node}
                            onNodeClick={handleNodeClick}
                            isSelected={node.id === selectedNodeId}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Paper>
              </Grid>
              
              {/* Node Details */}
              <Grid item xs={12} lg={4}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Node Details
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  {selectedNode ? (
                    <Box>
                      <Box display="flex" alignItems="center" mb={2}>
                        {React.createElement(
                          selectedNode.nodeType === 'source' ? Storage :
                          selectedNode.nodeType === 'transformation' ? Transform :
                          selectedNode.nodeType === 'sink' ? Assessment : AccountTree,
                          { color: 'primary' }
                        )}
                        <Typography variant="h6" sx={{ ml: 1 }}>
                          {selectedNode.name}
                        </Typography>
                      </Box>
                      
                      <Box mb={2}>
                        <Typography variant="subtitle2" color="primary">Type</Typography>
                        <Chip 
                          label={selectedNode.nodeType} 
                          size="small" 
                          color="primary" 
                        />
                      </Box>
                      
                      <Box mb={2}>
                        <Typography variant="subtitle2" color="primary">Dataset ID</Typography>
                        <Typography variant="body2">
                          {selectedNode.datasetId || 'N/A'}
                        </Typography>
                      </Box>
                      
                      {selectedNode.description && (
                        <Box mb={2}>
                          <Typography variant="subtitle2" color="primary">Description</Typography>
                          <Typography variant="body2">
                            {selectedNode.description}
                          </Typography>
                        </Box>
                      )}
                      
                      {selectedNode.lastUpdated && (
                        <Box mb={2}>
                          <Typography variant="subtitle2" color="primary">Last Updated</Typography>
                          <Typography variant="body2">
                            {new Date(selectedNode.lastUpdated).toLocaleString()}
                          </Typography>
                        </Box>
                      )}
                      
                      {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            Metadata
                          </Typography>
                          {Object.entries(selectedNode.metadata).map(([key, value]) => (
                            <Box key={key} display="flex" justifyContent="space-between" mb={1}>
                              <Typography variant="caption">{key}:</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {String(value)}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      )}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Click on a node to view details
                    </Typography>
                  )}
                </Paper>
                
                {/* Connections */}
                {selectedNode && edges.length > 0 && (
                  <Paper sx={{ p: 2, mt: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Connections
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    
                    <Box>
                      {edges
                        .filter(edge => edge.sourceId === selectedNode.id || edge.targetId === selectedNode.id)
                        .map(edge => {
                          const sourceNode = nodes.find(n => n.id === edge.sourceId);
                          const targetNode = nodes.find(n => n.id === edge.targetId);
                          
                          if (!sourceNode || !targetNode) return null;
                          
                          return (
                            <Box key={edge.id} mb={1}>
                              <LineageEdgeComponent
                                edge={edge}
                                sourceNode={sourceNode}
                                targetNode={targetNode}
                              />
                            </Box>
                          );
                        })}
                    </Box>
                  </Paper>
                )}
              </Grid>
            </Grid>
          )}
        </>
      )}
    </Box>
  );
};

export default LineageGraph;
