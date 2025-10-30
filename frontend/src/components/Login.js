import React, { useState } from 'react';
import { Lock } from 'lucide-react';

const Login = ({ onLogin }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Password provera - maksimalno 10 karaktera
    const correctPassword = process.env.REACT_APP_ADMIN_PASSWORD || 'admin123';
    
    if (password === correctPassword) {
      localStorage.setItem('isAuthenticated', 'true');
      onLogin(true);
    } else {
      setError('Pogrešan password! Pokušajte ponovo.');
      setPassword('');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo i Naziv */}
        <div className="text-center mb-8">
          <img 
            src={process.env.REACT_APP_LOGO_URL} 
            alt="Bua Luang Thai Spa Logo" 
            className="h-20 w-auto mx-auto mb-4"
          />
          <h1 className="text-3xl font-bold text-amber-900">Bua Luang Thai Spa</h1>
          <p className="text-amber-700 mt-2">Booking Management System</p>
        </div>

        {/* Login Form */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-amber-100 p-4 rounded-full">
              <Lock className="w-8 h-8 text-amber-700" />
            </div>
          </div>
          
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            Dobrodošli
          </h2>
          <p className="text-gray-600 text-center mb-6">
            Unesite password za pristup sistemu
          </p>

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label 
                htmlFor="password" 
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                maxLength={10}
                placeholder="Unesite password (max 10 karaktera)"
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
              Prijavi se
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Sistem za upravljanje terminima i klijentima
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-amber-700 text-sm mt-6">
          © 2025 Bua Luang Thai Spa - Sva prava zadržana
        </p>
      </div>
    </div>
  );
};

export default Login;
