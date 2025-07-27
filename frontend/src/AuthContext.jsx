import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null); // You might store username or user ID here

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      // In a real app, you'd decode the token or fetch user info
      // For now, we'll just assume a user is logged in if there's a token
      setUser({ id: 'some_id', username: 'user' }); // Placeholder user
    } else {
      localStorage.removeItem('token');
      setUser(null);
    }
  }, [token]);

  const login = (newToken) => {
    setToken(newToken);
  };

  const logout = () => {
    setToken(null);
    sessionStorage.removeItem('news'); // Clear sessionStorage for news on logout
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
