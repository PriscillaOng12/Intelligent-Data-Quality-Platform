import { createContext, useContext, useState } from 'react';
import axios from 'axios';

interface AuthContextValue {
  token: string | null;
  userEmail: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem('userEmail'));

  async function login(email: string, password: string) {
    const response = await axios.post(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/auth/login`, {
      email,
      password,
    });
    const { access_token } = response.data;
    setToken(access_token);
    setUserEmail(email);
    localStorage.setItem('token', access_token);
    localStorage.setItem('userEmail', email);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
  }

  function logout() {
    setToken(null);
    setUserEmail(null);
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    delete axios.defaults.headers.common['Authorization'];
  }

  const value: AuthContextValue = { token, userEmail, login, logout };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}