import { useState, useEffect, useCallback } from 'react';
import { getToken, clearToken, decodeToken } from '../lib/auth';
import { useNavigate } from 'react-router';

export function useAuth() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = getToken();
    if (token) {
      const decoded = decodeToken(token);
      if (decoded && decoded.exp * 1000 > Date.now()) {
        setUser({
          id: decoded.sub,
          nama: decoded.nama,
          peran: decoded.peran,
        });
      } else {
        clearToken();
        setUser(null);
      }
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    navigate('/login');
  }, [navigate]);

  return {
    user,
    isAuthenticated: !!user,
    logout,
  };
}
