import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon, Building, User, LogOut } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, currentOrg, organizations, setCurrentOrg, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <header
      style={{
        height: '60px',
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Building size={18} color="var(--accent)" />
          <select
            value={currentOrg?.id || ''}
            onChange={e => {
              const selected = organizations.find(o => String(o.id) === e.target.value);
              if (selected) setCurrentOrg(selected);
            }}
            style={{
              padding: '6px 12px',
              fontSize: '13px',
              fontWeight: 600,
              backgroundColor: 'var(--bg-surface)',
              borderColor: 'var(--border-subtle)',
              cursor: 'pointer',
              width: 'auto',
            }}
          >
            {organizations.map(org => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Dark/Light mode toggle */}
        <button
          onClick={toggleTheme}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: '8px',
            borderRadius: '6px',
            display: 'flex',
          }}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* User profile and logout */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
              <div
                style={{
                  width: '30px',
                  height: '30px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--accent-subtle)',
                  color: 'var(--accent)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                }}
              >
                {user.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>
              <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                {user.full_name || user.email}
              </span>
            </div>

            <button
              onClick={logout}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '12px' }}
              title="Sign Out"
            >
              <LogOut size={14} />
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
