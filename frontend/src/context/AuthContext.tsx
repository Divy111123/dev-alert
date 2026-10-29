import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, Organization } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  currentOrg: Organization | null;
  organizations: Organization[];
  login: (token: string, user: User) => void;
  logout: () => void;
  setCurrentOrg: (org: Organization) => void;
  refreshOrganizations: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('devalert_token'));
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrg, setCurrentOrgState] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUserData = async (authToken: string) => {
    try {
      // Fetch user profile
      const userRes = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (userRes.ok) {
        const userData = await userRes.json();
        setUser(userData);

        // Fetch organizations
        const orgsRes = await fetch('/api/v1/organizations', {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        if (orgsRes.ok) {
          const orgsData = await orgsRes.json();
          setOrganizations(orgsData);
          if (orgsData.length > 0) {
            const savedOrgId = localStorage.getItem('devalert_org_id');
            const matchedOrg = orgsData.find((o: Organization) => String(o.id) === savedOrgId) || orgsData[0];
            setCurrentOrgState(matchedOrg);
          }
        }
      } else {
        logout();
      }
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUserData(token);
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('devalert_token', newToken);
    setToken(newToken);
    setUser(newUser);
    fetchUserData(newToken);
  };

  const logout = () => {
    localStorage.removeItem('devalert_token');
    localStorage.removeItem('devalert_org_id');
    setToken(null);
    setUser(null);
    setOrganizations([]);
    setCurrentOrgState(null);
  };

  const setCurrentOrg = (org: Organization) => {
    setCurrentOrgState(org);
    localStorage.setItem('devalert_org_id', String(org.id));
  };

  const refreshOrganizations = async () => {
    if (token) {
      const orgsRes = await fetch('/api/v1/organizations', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (orgsRes.ok) {
        const orgsData = await orgsRes.json();
        setOrganizations(orgsData);
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        currentOrg,
        organizations,
        login,
        logout,
        setCurrentOrg,
        refreshOrganizations,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
