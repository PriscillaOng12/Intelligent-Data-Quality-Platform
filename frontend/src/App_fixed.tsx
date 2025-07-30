import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, Typography, Container } from '@mui/material';

import Layout from './components/common/Layout';
import Dashboard from './components/Dashboard/QualityOverview';
import DataCatalog from './components/DataCatalog/DatasetBrowser';
import DataLineage from './components/DataLineage/LineageGraph';
import AlertCenter from './components/Alerts/AlertCenter';
// import { useAuth } from './hooks/useAuth'; // Temporarily disabled for demo

const App: React.FC = () => {
  // Temporarily bypass authentication for demo purposes
  // const { isAuthenticated, isLoading } = useAuth();

  // if (isLoading) {
  //   return (
  //     <Box
  //       display="flex"
  //       justifyContent="center"
  //       alignItems="center"
  //       minHeight="100vh"
  //     >
  //       Loading...
  //     </Box>
  //   );
  // }

  // if (!isAuthenticated) {
  //   return <Navigate to="/login" replace />;
  // }

  // Simple error boundary to catch any component errors
  try {
    return (
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/catalog" element={<DataCatalog />} />
          <Route path="/lineage" element={<DataLineage />} />
          <Route path="/alerts" element={<AlertCenter />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Layout>
    );
  } catch (error) {
    return (
      <Container>
        <Box sx={{ mt: 4 }}>
          <Typography variant="h4" color="error" gutterBottom>
            Application Error
          </Typography>
          <Typography variant="body1">
            There was an error loading the application. Please check the console for details.
          </Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>
            Error: {error instanceof Error ? error.message : 'Unknown error'}
          </Typography>
        </Box>
      </Container>
    );
  }
};

export default App;
