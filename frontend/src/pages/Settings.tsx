import React from 'react';
import { useAuth } from '../lib/auth';

export default function SettingsPage() {
  const { userEmail, logout } = useAuth();
  return (
    <div>
      <h2>Settings</h2>
      <p><strong>Email:</strong> {userEmail}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}