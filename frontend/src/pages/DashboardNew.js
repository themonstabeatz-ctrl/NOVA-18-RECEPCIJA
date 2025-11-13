import React, { useState, useEffect } from 'react';
import { analyticsService, appointmentService, serviceService } from '../services/api';
import { TrendingUp, Users, DollarSign, Clock, Printer, LogOut, PieChart, BarChart3, List, X } from 'lucide-react';
import { BarChart, Bar, PieChart as RePieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Login from '../components/Login';

const DashboardNew = () => {
  const [period, setPeriod] = useState('week');
  const [detailedData, setDetailedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showAppointmentsList, setShowAppointmentsList] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    const authStatus = localStorage.getItem('isAuthenticated');
    if (authStatus === 'true') {
      setIsAuthenticated(true);
    } else {
      setShowLoginModal(true);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [period, isAuthenticated]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await analyticsService.getDetailed({ period });
      setDetailedData(response.data);
      console.log('Detailed analytics:', response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (status) => {
    setIsAuthenticated(status);
    setShowLoginModal(!status);
    if (status) {
      localStorage.setItem('isAuthenticated', 'true');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('isAuthenticated');
    setShowLoginModal(true);
  };

  const handlePrint = () => {
    window.print();
  };

  const getPeriodLabel = () => {
    switch(period) {
      case 'day': return 'Danas';
      case 'week': return 'Ova Nedelja';
      case 'month': return 'Ovaj Mesec';
      case 'year': return 'Ova Godina';
      default: return 'Nepoznato';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('sr-RS', { 
      style: 'currency', 
      currency: 'RSD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
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

  const handleShowAppointmentsList = () => {
    setShowAppointmentsList(true);
  };

  const COLORS = ['#C8A165', '#8B7355', '#D4AF37', '#CD853F'];
  const DISCOUNT_COLORS = {
    '0': '#10b981',
    '5': '#3b82f6',
    '10': '#f59e0b',
    '15': '#ef4444'
  };

  if (!isAuthenticated) {
    return (
      <Login 
        isOpen={showLoginModal} 
        onClose={() => setShowLoginModal(false)}
        onLogin={handleLogin}
      />
    );
  }

  if (loading || !detailedData) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Učitavanje...</div>
      </div>
    );
  }

  const { summary, by_category, by_discount, appointments_with_discount } = detailedData;

  // Prepare data for charts
  const categoryChartData = Object.entries(by_category)
    .filter(([_, data]) => data.appointments_count > 0)
    .map(([name, data]) => ({
      name: name,
      revenue: data.revenue,
      original: data.original_revenue,
      discount: data.discount_given,
      appointments: data.appointments_count
    }));

  const discountChartData = Object.entries(by_discount)
    .filter(([_, data]) => data.count > 0)
    .map(([percentage, data]) => ({
      name: `${percentage}% Popust`,
      count: data.count,
      revenue: data.revenue
    }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow print:shadow-none">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">CEO Dashboard</h1>
              <p className="text-gray-600 mt-1">Bua Luang Thai Spa - Analitika</p>
              {/* Show period in print */}
              <div className="hidden print:block mt-2">
                <p className="text-lg font-semibold text-[#C8A165]">
                  Izveštaj za: {getPeriodLabel()}
                </p>
                <p className="text-sm text-gray-600">
                  Period: {new Date(detailedData.start_date).toLocaleDateString('sr-RS')} - {new Date(detailedData.end_date).toLocaleDateString('sr-RS')}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Štampano: {new Date().toLocaleString('sr-RS')}
                </p>
              </div>
            </div>
            <div className="flex gap-3 print:hidden">
              <button
                onClick={handlePrint}
                className="flex items-center gap-2 px-4 py-2 bg-[#C8A165] text-white rounded-lg hover:bg-[#B89155] transition-colors"
              >
                <Printer className="w-4 h-4" />
                Štampaj {getPeriodLabel()}
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Odjavi se
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Period Selector */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 print:hidden">
        <div className="flex gap-3">
          {['day', 'week', 'month', 'year'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                period === p
                  ? 'bg-[#C8A165] text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {p === 'day' && 'Danas'}
              {p === 'week' && 'Ova Nedelja'}
              {p === 'month' && 'Ovaj Mesec'}
              {p === 'year' && 'Ova Godina'}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-600 mt-2">
          Period: {new Date(detailedData.start_date).toLocaleDateString('sr-RS')} - {new Date(detailedData.end_date).toLocaleDateString('sr-RS')}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Revenue */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Ukupna Zarada</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatCurrency(summary.total_revenue)}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-lg font-bold text-green-600">RSD</span>
              </div>
            </div>
            {summary.total_discount_given > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                Originalna: {formatCurrency(summary.total_original_revenue)}
              </p>
            )}
          </div>

          {/* Total Appointments */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Broj Termina</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {summary.total_appointments}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <Clock className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          {/* Total Discount Given */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Ukupan Popust</p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {formatCurrency(summary.total_discount_given)}
                </p>
              </div>
              <div className="p-3 bg-red-100 rounded-full">
                <TrendingUp className="w-6 h-6 text-red-600" />
              </div>
            </div>
            {summary.total_original_revenue > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                {summary.discount_percentage.toFixed(1)}% od ukupne zarade
              </p>
            )}
          </div>

          {/* Appointments with Discount */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Sa Popustom</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {appointments_with_discount.length}
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <Users className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {summary.total_appointments > 0 
                ? ((appointments_with_discount.length / summary.total_appointments) * 100).toFixed(1)
                : 0}% svih termina
            </p>
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Pregled Po Kategorijama</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(by_category).map(([categoryName, categoryData], index) => (
            <div key={categoryName} className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">{categoryName}</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-gray-600">Termini</p>
                  <p className="text-xl font-bold text-gray-900">{categoryData.appointments_count}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Zarada</p>
                  <p className="text-lg font-semibold" style={{color: COLORS[index % COLORS.length]}}>
                    {formatCurrency(categoryData.revenue)}
                  </p>
                  {categoryData.discount_given > 0 && (
                    <p className="text-xs text-gray-500">
                      Original: {formatCurrency(categoryData.original_revenue)}
                    </p>
                  )}
                </div>
                {categoryData.discount_given > 0 && (
                  <div>
                    <p className="text-xs text-gray-600">Popust Dat</p>
                    <p className="text-sm font-semibold text-red-600">
                      -{formatCurrency(categoryData.discount_given)}
                    </p>
                  </div>
                )}
                <div className="flex gap-4 text-xs">
                  <div>
                    <p className="text-gray-600">Sa popustom</p>
                    <p className="font-semibold text-blue-600">{categoryData.with_discount}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Bez popusta</p>
                    <p className="font-semibold text-green-600">{categoryData.without_discount}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Revenue by Category Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Zarada Po Kategorijama
            </h3>
            {categoryChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={categoryChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={12} />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                  <Bar dataKey="revenue" fill="#C8A165" name="Zarada sa popustom" />
                  <Bar dataKey="original" fill="#D4AF37" name="Originalna zarada" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 text-center py-10">Nema podataka</p>
            )}
          </div>

          {/* Discount Distribution Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <PieChart className="w-5 h-5" />
              Distribucija Popusta
            </h3>
            {discountChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <RePieChart>
                  <Pie
                    data={discountChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({name, count}) => `${name}: ${count}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {discountChartData.map((entry, index) => {
                      const percentage = entry.name.match(/\d+/)[0];
                      return <Cell key={`cell-${index}`} fill={DISCOUNT_COLORS[percentage] || '#999'} />;
                    })}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </RePieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 text-center py-10">Nema podataka</p>
            )}
          </div>
        </div>
      </div>

      {/* Appointments with Discount Table */}
      {appointments_with_discount.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Termini Sa Popustom</h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Klijent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Telefon
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Datum/Vreme
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Usluga
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Kategorija
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Original
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Popust
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Konačna Cena
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ušteda
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {appointments_with_discount.map((apt) => (
                    <tr key={apt.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {apt.client_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {apt.client_phone}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(apt.start_time).toLocaleString('sr-RS', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {apt.service_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {apt.category}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                        {formatCurrency(apt.original_price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                          -{apt.discount_percentage}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 text-right">
                        {formatCurrency(apt.discounted_price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600 text-right">
                        {formatCurrency(apt.discount_amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Print Styles */}
      <style>{`
        @media print {
          body { background: white; }
          .print\:hidden { display: none !important; }
          .print\:shadow-none { box-shadow: none !important; }
          .print\:block { display: block !important; }
          @page { 
            size: A4 landscape; 
            margin: 1cm; 
          }
          /* Add page break after charts */
          .bg-white.rounded-lg.shadow.p-6:has(.recharts-wrapper) {
            page-break-after: avoid;
          }
          /* Keep tables together */
          table {
            page-break-inside: avoid;
          }
        }
      `}</style>
    </div>
  );
};

export default DashboardNew;
