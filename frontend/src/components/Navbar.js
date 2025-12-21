import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Calendar, Users, Briefcase, Settings, Menu, X, Bell, CreditCard } from 'lucide-react';
import { appointmentService } from '../services/api';

const Navbar = () => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unviewedCount, setUnviewedCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);

  const navItems = [
    // Dashboard is hidden - accessible only via logo click (secret feature)
    { path: '/appointments', label: 'Termini', icon: Calendar },
    { path: '/therapists', label: 'Terapeuti', icon: Users },
    { path: '/services', label: 'Usluge', icon: Briefcase },
    { path: '/spa-cards', label: 'SPA Kartice', icon: CreditCard },
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
      // Automatically mark all as viewed when opening notification modal
      if (unviewedCount > 0) {
        try {
          await appointmentService.markAllViewed();
          setUnviewedCount(0);
        } catch (error) {
          console.error('Error auto-marking viewed:', error);
        }
      }
    }
    setShowNotifications(!showNotifications);
  };

  const markAllViewed = async () => {
    try {
      await appointmentService.markAllViewed();
      setUnviewedCount(0);
      setNotifications([]);
      setShowNotifications(false);
      // Reload count to ensure sync
      await loadUnviewedCount();
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
              {/* Hidden Dashboard access - only logo is clickable (smaller sensitive area) */}
              <Link to="/" className="cursor-default">
                <img 
                  src={process.env.REACT_APP_LOGO_URL} 
                  alt="Bua Luang Thai Spa Logo" 
                  className="h-12 sm:h-14 md:h-16 w-auto"
                />
              </Link>
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

      {/* Notification Modal */}
      {showNotifications && (
        <div className="absolute right-4 top-16 w-96 bg-white rounded-lg shadow-xl border z-50" data-testid="notification-modal">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">
              Notifikacije {unviewedCount > 0 && `(${unviewedCount})`}
            </h3>
            <div className="flex gap-2">
              {unviewedCount > 0 && (
                <button
                  onClick={markAllViewed}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Označi sve kao pregledano
                </button>
              )}
              <button
                onClick={() => setShowNotifications(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Bell className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>Nema novih notifikacija</p>
              </div>
            ) : (
              <div className="divide-y">
                {notifications.map((notification) => (
                  <div key={notification.id} className="p-4 hover:bg-gray-50 border-l-4 border-amber-500 transition-colors">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        <Calendar className="w-5 h-5 text-amber-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-bold text-amber-700 mb-2">
                          🔔 Nova online rezervacija
                        </p>
                        
                        {/* Client Info */}
                        <p className="text-lg font-semibold text-gray-900">
                          {notification.client_first_name} {notification.client_last_name}
                        </p>
                        
                        {/* Service & Date/Time */}
                        <div className="mt-3 space-y-2 bg-amber-50 p-3 rounded-lg">
                          <div className="flex items-start gap-2">
                            <span className="text-amber-700 font-semibold">💆‍♀️ Usluga:</span>
                            <div className="font-medium text-gray-800 flex-1">
                              {/* COUPLES BOOKING: Show all services from snapshot */}
                              {notification.is_couples_booking && (notification.person1_services_snapshot || notification.person2_services_snapshot) ? (
                                <div className="space-y-2">
                                  {notification.person1_services_snapshot && notification.person1_services_snapshot.length > 0 && (
                                    <div>
                                      <span className="text-xs text-amber-600 font-semibold">Osoba 1:</span>
                                      <ul className="list-disc list-inside text-sm">
                                        {notification.person1_services_snapshot.map((svc, idx) => (
                                          <li key={`p1-${idx}`}>{svc.name} - {svc.duration}min ({svc.price?.toLocaleString()} RSD)</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  {notification.person2_services_snapshot && notification.person2_services_snapshot.length > 0 && (
                                    <div>
                                      <span className="text-xs text-amber-600 font-semibold">Osoba 2:</span>
                                      <ul className="list-disc list-inside text-sm">
                                        {notification.person2_services_snapshot.map((svc, idx) => (
                                          <li key={`p2-${idx}`}>{svc.name} - {svc.duration}min ({svc.price?.toLocaleString()} RSD)</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  {notification.pricing_breakdown && (
                                    <div className="text-xs text-gray-500 mt-1">
                                      Breakdown: {notification.pricing_breakdown}
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <span>{notification.service_name || 'N/A'}</span>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <span className="text-amber-700 font-semibold">📅 Datum i vreme:</span>
                            <span className="text-gray-700">
                              {formatDateTime(notification.start_time)}
                            </span>
                          </div>
                          
                          {notification.service_duration && (
                            <div className="flex items-center gap-2">
                              <span className="text-amber-700 font-semibold">⏱️ Trajanje:</span>
                              <span className="text-gray-700">
                                {notification.service_duration} min
                              </span>
                            </div>
                          )}
                          
                          {notification.therapist_name && (
                            <div className="flex items-center gap-2">
                              <span className="text-amber-700 font-semibold">👤 Terapeut:</span>
                              <span className="text-gray-700">
                                {notification.therapist_name}
                              </span>
                            </div>
                          )}
                        </div>
                        
                        {/* Price */}
                        {notification.service_price && (
                          <div className="mt-3 p-2 bg-green-50 rounded-lg border border-green-200">
                            {notification.discount_percentage > 0 ? (
                              <div>
                                <p className="text-xs text-gray-500 line-through">
                                  Original: {notification.original_price.toLocaleString()} RSD
                                </p>
                                <p className="text-base font-bold text-green-700 flex items-center gap-2">
                                  💰 Cena: {notification.service_price.toLocaleString()} RSD
                                  <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
                                    -{notification.discount_percentage}%
                                  </span>
                                </p>
                              </div>
                            ) : (
                              <p className="text-base font-bold text-green-700 flex items-center gap-2">
                                💰 Cena: {notification.service_price.toLocaleString()} RSD
                              </p>
                            )}
                          </div>
                        )}
                        
                        {/* Contact Info */}
                        <div className="mt-3 space-y-1 text-sm">
                          {notification.client_phone && (
                            <p className="text-gray-600 flex items-center gap-2">
                              <span className="font-semibold">📞 Telefon:</span>
                              <a href={`tel:${notification.client_phone}`} className="text-blue-600 hover:underline">
                                {notification.client_phone}
                              </a>
                            </p>
                          )}
                          {notification.client_email && (
                            <p className="text-gray-600 flex items-center gap-2">
                              <span className="font-semibold">📧 Email:</span>
                              <a href={`mailto:${notification.client_email}`} className="text-blue-600 hover:underline">
                                {notification.client_email}
                              </a>
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
