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

  const formatDate = (dateTimeStr) => {
    const date = new Date(dateTimeStr);
    return date.toLocaleDateString('sr-RS', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
  };

  const formatTime = (dateTimeStr) => {
    const date = new Date(dateTimeStr);
    return date.toLocaleTimeString('sr-RS', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Group appointments by date (day)
  const groupAppointmentsByDay = () => {
    if (!detailedData?.appointments_by_service) return {};
    
    const grouped = {};
    detailedData.appointments_by_service.forEach(serviceData => {
      serviceData.appointments?.forEach(apt => {
        const date = new Date(apt.start_time);
        const dateKey = date.toISOString().split('T')[0]; // YYYY-MM-DD
        
        if (!grouped[dateKey]) {
          grouped[dateKey] = [];
        }
        
        grouped[dateKey].push({
          ...apt,
          service_name: serviceData.service_name,
          service_duration: serviceData.service_duration
        });
      });
    });
    
    // Sort appointments within each day by start_time
    Object.keys(grouped).forEach(dateKey => {
      grouped[dateKey].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
    });
    
    return grouped;
  };

  const handleShowAppointmentsList = () => {
    setShowAppointmentsList(true);
  };

  const handlePrintListing = () => {
    const printContent = document.getElementById('appointments-listing-print');
    if (!printContent) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Listing Rezervacija - ${getPeriodLabel()}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #C8A165; margin-bottom: 20px; }
            .summary { background: #f9fafb; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center; }
            .summary-item p:first-child { color: #6b7280; font-size: 14px; }
            .summary-item p:last-child { font-size: 24px; font-weight: bold; color: #1f2937; }
            .day-section { margin-bottom: 30px; page-break-inside: avoid; }
            .day-header { background: #C8A165; color: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 10px; font-size: 18px; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            th { background: #f3f4f6; padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb; font-size: 12px; text-transform: uppercase; }
            td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }
            .total-row { background: #f9fafb; font-weight: bold; }
            .price { color: #059669; font-weight: bold; }
            @media print {
              .no-print { display: none; }
              body { margin: 0; }
            }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
  };

  const handleDeleteAllAppointments = async () => {
    if (!window.confirm(`Da li ste sigurni da želite da obrišete SVE rezervacije za period "${getPeriodLabel()}"?\n\nOvo će obrisati ${detailedData?.total_appointments || 0} rezervacija i ne može se poništiti!`)) {
      return;
    }
    
    try {
      const grouped = groupAppointmentsByDay();
      const allAppointmentIds = Object.values(grouped).flat().map(apt => apt.id);
      
      // Delete each appointment
      for (const id of allAppointmentIds) {
        await appointmentService.delete(id);
      }
      
      alert(`Uspešno obrisano ${allAppointmentIds.length} rezervacija!`);
      setShowAppointmentsList(false);
      fetchData(); // Reload dashboard data
    } catch (error) {
      console.error('Error deleting appointments:', error);
      alert('Greška pri brisanju rezervacija. Pokušajte ponovo.');
    }
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
        <div className="flex gap-3 items-center justify-between">
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
          
          {/* Appointments List Button */}
          <button
            onClick={handleShowAppointmentsList}
            className="flex items-center gap-2 px-6 py-2 bg-amber-600 text-white rounded-lg font-medium hover:bg-amber-700 transition-colors shadow-md"
          >
            <List className="w-5 h-5" />
            Listing Rezervacija
          </button>
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

      {/* Appointments List Modal */}
      {showAppointmentsList && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="bg-amber-600 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <List className="w-6 h-6" />
                <h2 className="text-2xl font-bold">
                  Listing Rezervacija - {getPeriodLabel()}
                </h2>
              </div>
              <div className="flex items-center gap-3">
                {/* Print Button */}
                <button
                  onClick={handlePrintListing}
                  className="flex items-center gap-2 px-4 py-2 bg-white text-amber-600 rounded-lg font-medium hover:bg-amber-50 transition-colors"
                >
                  <Printer className="w-5 h-5" />
                  Štampaj
                </button>
                {/* Delete All Button */}
                <button
                  onClick={handleDeleteAllAppointments}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
                >
                  <X className="w-5 h-5" />
                  Obriši Sve
                </button>
                {/* Close Button */}
                <button
                  onClick={() => setShowAppointmentsList(false)}
                  className="text-white hover:bg-amber-700 rounded-full p-2 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
              <div id="appointments-listing-print">
                {detailedData?.appointments_by_service && detailedData.appointments_by_service.length > 0 ? (
                  <div className="space-y-6">
                    {/* Summary Info */}
                    <div className="summary bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                      <div className="summary-grid grid grid-cols-3 gap-4 text-center">
                        <div className="summary-item">
                          <p className="text-sm text-gray-600">Ukupno Rezervacija</p>
                          <p className="text-2xl font-bold text-amber-700">{detailedData.total_appointments}</p>
                        </div>
                        <div className="summary-item">
                          <p className="text-sm text-gray-600">Ukupna Zarada</p>
                          <p className="text-2xl font-bold text-green-700">{formatCurrency(detailedData.total_revenue)}</p>
                        </div>
                        <div className="summary-item">
                          <p className="text-sm text-gray-600">Period</p>
                          <p className="text-lg font-semibold text-gray-700">
                            {new Date(detailedData.start_date).toLocaleDateString('sr-RS')} - {new Date(detailedData.end_date).toLocaleDateString('sr-RS')}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Appointments by Day */}
                    {(() => {
                      const groupedByDay = groupAppointmentsByDay();
                      const sortedDates = Object.keys(groupedByDay).sort();
                      let globalCounter = 1;
                      
                      return sortedDates.map((dateKey) => {
                        const dayAppointments = groupedByDay[dateKey];
                        const dayTotal = dayAppointments.reduce((sum, apt) => sum + apt.total_price, 0);
                        
                        return (
                          <div key={dateKey} className="day-section mb-6">
                            {/* Day Header */}
                            <div className="day-header bg-amber-600 text-white px-4 py-3 rounded-lg mb-3 flex items-center justify-between">
                              <h3 className="text-lg font-bold">
                                📅 {formatDate(dayAppointments[0].start_time)}
                              </h3>
                              <span className="text-sm bg-white bg-opacity-20 px-3 py-1 rounded-full">
                                {dayAppointments.length} rezervacija
                              </span>
                            </div>

                            {/* Day Appointments Table */}
                            <div className="overflow-x-auto">
                              <table className="min-w-full bg-white border border-gray-200 rounded-lg">
                                <thead className="bg-gray-100">
                                  <tr>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b w-16">
                                      #
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b">
                                      Vreme
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b">
                                      Klijent
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b">
                                      Usluga
                                    </th>
                                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider border-b">
                                      Cena
                                    </th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                  {dayAppointments.map((apt) => {
                                    const rowNumber = globalCounter++;
                                    return (
                                      <tr key={apt.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-4 py-3 text-sm text-gray-600 font-bold">
                                          {rowNumber}
                                        </td>
                                        <td className="px-4 py-3">
                                          <span className="text-sm font-semibold text-gray-900">
                                            {formatTime(apt.start_time)}
                                          </span>
                                        </td>
                                        <td className="px-4 py-3">
                                          <p className="text-sm font-semibold text-gray-900">
                                            {apt.client_first_name} {apt.client_last_name}
                                          </p>
                                          {apt.client_phone && (
                                            <p className="text-xs text-gray-500 mt-1">
                                              📞 {apt.client_phone}
                                            </p>
                                          )}
                                        </td>
                                        <td className="px-4 py-3">
                                          <p className="text-sm font-medium text-gray-900">
                                            {apt.service_name}
                                          </p>
                                          <p className="text-xs text-gray-500 mt-1">
                                            ⏱️ {apt.service_duration || 'N/A'} min
                                          </p>
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                          {apt.discount_percentage > 0 ? (
                                            <div>
                                              <p className="text-xs text-gray-400 line-through">
                                                {formatCurrency(apt.original_price)}
                                              </p>
                                              <div className="flex items-center justify-end gap-2">
                                                <span className="price text-sm font-bold text-green-700">
                                                  {formatCurrency(apt.total_price)}
                                                </span>
                                                <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                                                  -{apt.discount_percentage}%
                                                </span>
                                              </div>
                                            </div>
                                          ) : (
                                            <span className="price text-sm font-bold text-green-700">
                                              {formatCurrency(apt.total_price)}
                                            </span>
                                          )}
                                        </td>
                                      </tr>
                                    );
                                  })}
                                </tbody>
                                <tfoot className="bg-gray-50">
                                  <tr className="total-row">
                                    <td colSpan="4" className="px-4 py-3 text-right text-sm font-bold text-gray-900">
                                      Ukupno za dan:
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                      <span className="price text-base font-bold text-green-700">
                                        {formatCurrency(dayTotal)}
                                      </span>
                                    </td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>
                          </div>
                        );
                      });
                    })()}

                    {/* Grand Total */}
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-6 mt-6">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xl font-bold text-gray-900">
                          UKUPNA ZARADA ZA PERIOD:
                        </h3>
                        <p className="text-3xl font-bold text-green-700">
                          {formatCurrency(detailedData.total_revenue)}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <List className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">Nema rezervacija za izabrani period</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardNew;
