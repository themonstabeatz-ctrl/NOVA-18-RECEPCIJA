import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Calendar, Users, Briefcase, Settings, Menu, X, Bell } from 'lucide-react';
import { appointmentService } from '../services/api';

const Navbar = () => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unviewedCount, setUnviewedCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/appointments', label: 'Termini', icon: Calendar },
    { path: '/therapists', label: 'Terapeuti', icon: Users },
    { path: '/services', label: 'Usluge', icon: Briefcase },
    { path: '/settings', label: 'Podešavanja', icon: Settings },
  ];

  // Load unviewed count on mount and every 30 seconds
  useEffect(() => {
    loadUnviewedCount();
    const interval = setInterval(loadUnviewedCount, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadUnviewedCount = async () => {
    try {
      const response = await appointmentService.getUnviewedCount();
      setUnviewedCount(response.data.count);
    } catch (error) {
      console.error('Error loading unviewed count:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const response = await appointmentService.getUnviewedList();
      setNotifications(response.data);
    } catch (error) {
      console.error('Error loading notifications:', error);
    }
  };

  const handleBellClick = async () => {
    if (!showNotifications) {
      await loadNotifications();
    }
    setShowNotifications(!showNotifications);
  };

  const markAllViewed = async () => {
    try {
      await appointmentService.markAllViewed();
      setUnviewedCount(0);
      setNotifications([]);
      setShowNotifications(false);
    } catch (error) {
      console.error('Error marking all viewed:', error);
    }
  };

  const formatDateTime = (dateTimeStr) => {
    const date = new Date(dateTimeStr);
    return date.toLocaleString('sr-RS', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center gap-2 sm:gap-3">
              <img 
                src={process.env.REACT_APP_LOGO_URL} 
                alt="Bua Luang Thai Spa Logo" 
                className="h-12 sm:h-14 md:h-16 w-auto"
              />
              <div className="flex flex-col justify-center">
                <span className="text-sm sm:text-lg md:text-xl font-bold text-amber-700 leading-tight">Bua Luang</span>
                <span className="text-sm sm:text-lg md:text-xl font-bold text-amber-700 leading-tight">Thai Spa</span>
              </div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:space-x-4 lg:space-x-8 items-center">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`inline-flex items-center px-2 lg:px-3 py-2 border-b-2 text-xs lg:text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-amber-700 text-amber-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                  data-testid={`nav-${item.label.toLowerCase()}`}
                >
                  <Icon className="w-4 h-4 mr-1 lg:mr-2" />
                  {item.label}
                </Link>
              );
            })}
            
            {/* Notification Bell */}
            <button
              onClick={handleBellClick}
              className="relative p-2 text-gray-500 hover:text-gray-700 focus:outline-none"
              data-testid="notification-bell"
            >
              <Bell className="w-5 h-5" />
              {unviewedCount > 0 && (
                <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
                  {unviewedCount}
                </span>
              )}
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-amber-700"
              data-testid="mobile-menu-btn"
            >
              <span className="sr-only">Open main menu</span>
              {mobileMenuOpen ? (
                <X className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200" data-testid="mobile-menu">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center px-3 py-3 rounded-md text-base font-medium transition-colors ${
                    isActive
                      ? 'bg-amber-50 text-amber-900 border-l-4 border-amber-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                  data-testid={`mobile-nav-${item.label.toLowerCase()}`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
