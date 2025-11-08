import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import MobileHint from './components/MobileHint';
import DashboardNew from './pages/DashboardNew';
import Appointments from './pages/Appointments';
import Therapists from './pages/Therapists';
import Services from './pages/Services';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<DashboardNew />} />
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
