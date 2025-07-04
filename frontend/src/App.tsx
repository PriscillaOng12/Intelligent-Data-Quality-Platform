import React from 'react';
import { Navigate, Route, Routes, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth';

import OverviewPage from './pages/Overview';
import IncidentsPage from './pages/Incidents';
import DatasetsPage from './pages/Datasets';
import RulesPage from './pages/Rules';
import LineagePage from './pages/Lineage';
import SettingsPage from './pages/Settings';
import LoginPage from './pages/Login';

function ProtectedRoutes() {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div className="app-container" style={{ display: 'flex', minHeight: '100vh' }}>
      <nav style={{ width: '200px', background: '#f5f5f5', padding: '1rem' }}>
        <h3>IDQP</h3>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          <li><Link to="/">Overview</Link></li>
          <li><Link to="/incidents">Incidents</Link></li>
          <li><Link to="/datasets">Datasets</Link></li>
          <li><Link to="/rules">Rules</Link></li>
          <li><Link to="/lineage">Lineage</Link></li>
          <li><Link to="/settings">Settings</Link></li>
        </ul>
      </nav>
      <main style={{ flexGrow: 1, padding: '1rem' }}>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/datasets" element={<DatasetsPage />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route path="/lineage" element={<LineagePage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<ProtectedRoutes />} />
      </Routes>
    </AuthProvider>
  );
}