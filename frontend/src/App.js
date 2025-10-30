import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import MobileHint from './components/MobileHint';
import Login from './components/Login';
import Dashboard from './pages/Dashboard';
import Appointments from './pages/Appointments';
import Therapists from './pages/Therapists';
import Services from './pages/Services';
import Settings from './pages/Settings';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check authentication status on mount
  useEffect(() => {
    const authStatus = localStorage.getItem('isAuthenticated');
    if (authStatus === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = (status) => {
    setIsAuthenticated(status);
  };

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    setIsAuthenticated(false);
  };

  // Protected Dashboard component
  const ProtectedDashboard = () => {
    if (!isAuthenticated) {
      return <Login onLogin={handleLogin} />;
    }
    return <Dashboard onLogout={handleLogout} />;
  };

  return (
    <div className="App">
      <BrowserRouter>
        {isAuthenticated && <Navbar />}
        <Routes>
          <Route path="/" element={<ProtectedDashboard />} />
          <Route path="/appointments" element={<Appointments />} />
          <Route path="/therapists" element={<Therapists />} />
          <Route path="/services" element={<Services />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <MobileHint />
      </BrowserRouter>
    </div>
  );
}

export default App;
