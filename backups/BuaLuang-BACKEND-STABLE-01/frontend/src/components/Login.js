import React, { useState } from 'react';
import { Lock, X } from 'lucide-react';

const Login = ({ onLogin, onClose }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Password provera - maksimalno 10 karaktera
    const correctPassword = process.env.REACT_APP_DASHBOARD_PASSWORD || 'studio149';
    
    if (password === correctPassword) {
      localStorage.setItem('isAuthenticated', 'true');
      onLogin(true);
      setError('');
      setPassword('');
    } else {
      setError('Pogrešan password! Pokušajte ponovo.');
      setPassword('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center px-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-6 h-6" />
        </button>

        {/* Logo */}
        <div className="flex items-center justify-center mb-6">
          <div className="bg-amber-100 p-4 rounded-full">
            <Lock className="w-8 h-8 text-amber-700" />
          </div>
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
          Dashboard Pristup
        </h2>
        <p className="text-gray-600 text-center mb-6">
          Unesite vašu šifru za pristup Dashboard-u
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label 
              htmlFor="password" 
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Šifra
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              maxLength={10}
              placeholder="Unesite šifru (max 10 karaktera)"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              autoFocus
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Maksimalno 10 karaktera
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600 text-center">{error}</p>
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-amber-700 text-white py-3 rounded-lg font-semibold hover:bg-amber-800 transition-colors shadow-md"
          >
            Potvrdi
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
