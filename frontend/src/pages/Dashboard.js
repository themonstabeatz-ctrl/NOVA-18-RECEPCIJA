import React, { useState, useEffect } from 'react';
import { analyticsService } from '../services/api';
import { TrendingUp, Users, DollarSign, Clock, Printer, LogOut } from 'lucide-react';
import Login from '../components/Login';

const Dashboard = () => {
  const [period, setPeriod] = useState('week');
  const [therapistStats, setTherapistStats] = useState([]);
  const [revenueData, setRevenueData] = useState(null);
  const [clientData, setClientData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

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
      const [therapistRes, revenueRes, clientRes] = await Promise.all([
        analyticsService.getTherapistStats({ period }),
        analyticsService.getRevenue({ period }),
        analyticsService.getClients({ period }),
      ]);

      setTherapistStats(therapistRes.data.statistics || []);
      setRevenueData(revenueRes.data);
      setClientData(clientRes.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (status) => {
    setIsAuthenticated(status);
    setShowLoginModal(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    setIsAuthenticated(false);
    setShowLoginModal(true);
  };

  const handleCloseModal = () => {
    // Redirect to appointments page if user closes modal without logging in
    window.location.href = '/appointments';
  };

  const periodLabels = {
    day: 'Danas',
    week: 'Ova nedelja',
    month: 'Ovaj mesec',
    year: 'Ova godina',
  };

  const totalRevenue = revenueData?.total_revenue || 0;
  const totalClients = clientData?.total_clients || 0;
  const totalAppointments = revenueData?.appointments_count || 0;
  const totalHours = therapistStats.reduce((sum, t) => sum + t.total_hours, 0);

  const handlePrintReport = () => {
    const printWindow = window.open('', '_blank');
    const currentDate = new Date().toLocaleDateString('sr-RS');
    
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CEO Dashboard Izveštaj - ${periodLabels[period]}</title>
        <style>
          @page {
            size: A4;
            margin: 2cm;
          }
          body {
            font-family: 'Arial', sans-serif;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
          }
          .header {
            text-align: center;
            border-bottom: 3px solid #d97706;
            padding-bottom: 20px;
            margin-bottom: 30px;
          }
          .header img {
            max-width: 150px;
            height: auto;
            margin-bottom: 10px;
          }
          .header h1 {
            color: #92400e;
            margin: 10px 0;
            font-size: 24px;
          }
          .period-info {
            background: #fef3c7;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            border-left: 4px solid #d97706;
          }
          .summary-cards {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
          }
          .card {
            background: #fef3c7;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #d97706;
          }
          .card-label {
            font-size: 14px;
            color: #78350f;
            font-weight: bold;
            margin-bottom: 10px;
          }
          .card-value {
            font-size: 32px;
            color: #92400e;
            font-weight: bold;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
          }
          th {
            background: #fde68a;
            color: #78350f;
            padding: 12px;
            text-align: left;
            border: 1px solid #d97706;
            font-weight: bold;
          }
          td {
            padding: 10px 12px;
            border: 1px solid #fde68a;
            background: white;
          }
          tr:nth-child(even) td {
            background: #fef3c7;
          }
          .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #fde68a;
            text-align: center;
            color: #d97706;
            font-size: 12px;
          }
          @media print {
            body {
              padding: 0;
            }
            .no-print {
              display: none;
            }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <img src="${process.env.REACT_APP_LOGO_URL}" alt="Bua Luang Thai Spa Logo" />
          <h1>Bua Luang Thai Spa</h1>
          <p style="color: #92400e; margin: 0; font-size: 16px;">CEO DASHBOARD IZVEŠTAJ</p>
        </div>

        <div class="period-info">
          <h2 style="color: #78350f; margin: 0; font-size: 18px;">Period: ${periodLabels[period]}</h2>
          <p style="color: #92400e; margin: 5px 0 0 0; font-size: 14px;">Izveštaj kreiran: ${currentDate}</p>
        </div>

        <div class="summary-cards">
          <div class="card">
            <div class="card-label">Ukupna zarada</div>
            <div class="card-value">${totalRevenue.toLocaleString()} RSD</div>
          </div>
          <div class="card">
            <div class="card-label">Broj klijenata</div>
            <div class="card-value">${totalClients}</div>
          </div>
          <div class="card">
            <div class="card-label">Broj termina</div>
            <div class="card-value">${totalAppointments}</div>
          </div>
          <div class="card">
            <div class="card-label">Ukupno sati</div>
            <div class="card-value">${totalHours.toFixed(1)}h</div>
          </div>
        </div>

        <h2 style="color: #78350f; margin-top: 30px; margin-bottom: 15px;">Statistike po terapeutu</h2>
        <table>
          <thead>
            <tr>
              <th>Terapeut</th>
              <th>Radni sati</th>
              <th>Zarada</th>
              <th>Broj klijenata</th>
            </tr>
          </thead>
          <tbody>
            ${therapistStats.length === 0 ? `
              <tr><td colspan="4" style="text-align: center; color: #999;">Nema podataka za izabrani period</td></tr>
            ` : therapistStats.map(therapist => `
              <tr>
                <td><strong>${therapist.therapist_name}</strong></td>
                <td>${therapist.total_hours.toFixed(1)}h</td>
                <td>${therapist.total_revenue.toLocaleString()} RSD</td>
                <td>${therapist.client_count}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <div class="footer">
          <p>© Bua Luang Thai Spa - Izveštaj generisan ${currentDate}</p>
        </div>

        <div class="no-print" style="text-align: center; margin-top: 30px;">
          <button onclick="window.print()" style="background: #d97706; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; margin-right: 10px;">
            🖨️ Štampaj
          </button>
          <button onclick="window.close()" style="background: #6b7280; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">
            ✖ Zatvori
          </button>
        </div>
      </body>
      </html>
    `;

    printWindow.document.write(html);
    printWindow.document.close();
  };

  return (
    <div className="min-h-screen bg-gray-50 py-4 md:py-8" data-testid="dashboard-page">
      {/* Login Modal */}
      {showLoginModal && (
        <Login onLogin={handleLogin} onClose={handleCloseModal} />
      )}

      {/* Dashboard Content */}
      {!showLoginModal && isAuthenticated && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-6 md:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900" data-testid="dashboard-title">CEO Dashboard</h1>
            <p className="mt-2 text-sm md:text-base text-gray-600">Pregled performansi i statistike</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handlePrintReport}
              className="inline-flex items-center justify-center px-4 py-2 bg-amber-700 text-white rounded-lg hover:bg-amber-800 transition-colors shadow-md"
              data-testid="print-report-btn"
            >
              <Printer className="w-5 h-5 mr-2" />
              Štampaj izveštaj
            </button>
            <button
              onClick={handleLogout}
              className="inline-flex items-center justify-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors shadow-md"
              data-testid="logout-btn"
            >
              <LogOut className="w-5 h-5 mr-2" />
              Odjavi se
            </button>
          </div>
        </div>

        {/* Period Selector */}
        <div className="mb-4 md:mb-6 flex flex-wrap gap-2" data-testid="period-selector">
          {Object.entries(periodLabels).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setPeriod(key)}
              className={`flex-1 sm:flex-none px-3 md:px-4 py-2 rounded-lg font-medium transition-colors text-sm md:text-base ${
                period === key
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
              data-testid={`period-${key}`}
            >
              {label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-12" data-testid="dashboard-loading">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6 md:mb-8">
              <div className="bg-white rounded-lg shadow p-6" data-testid="total-revenue-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Ukupna zarada</p>
                    <p className="text-2xl font-bold text-gray-900 mt-2" data-testid="total-revenue">
                      {totalRevenue.toLocaleString()} RSD
                    </p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-full">
                    <DollarSign className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6" data-testid="total-clients-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Broj klijenata</p>
                    <p className="text-2xl font-bold text-gray-900 mt-2" data-testid="total-clients">
                      {totalClients}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-100 rounded-full">
                    <Users className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6" data-testid="total-appointments-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Broj termina</p>
                    <p className="text-2xl font-bold text-gray-900 mt-2" data-testid="total-appointments">
                      {totalAppointments}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-100 rounded-full">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6" data-testid="total-hours-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Ukupno sati</p>
                    <p className="text-2xl font-bold text-gray-900 mt-2" data-testid="total-hours">
                      {totalHours.toFixed(1)}h
                    </p>
                  </div>
                  <div className="p-3 bg-orange-100 rounded-full">
                    <Clock className="w-6 h-6 text-orange-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Therapist Statistics Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden" data-testid="therapist-stats-table">
              <div className="px-4 md:px-6 py-3 md:py-4 border-b border-gray-200">
                <h2 className="text-base md:text-lg font-semibold text-gray-900">Statistike po terapeutu</h2>
              </div>
              <div className="overflow-x-auto -webkit-overflow-scrolling-touch">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                        Terapeut
                      </th>
                      <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                        Sati
                      </th>
                      <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                        Zarada
                      </th>
                      <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                        Klijenti
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {therapistStats.length === 0 ? (
                      <tr>
                        <td colSpan="4" className="px-3 md:px-6 py-4 text-center text-gray-500 text-sm">
                          Nema podataka za izabrani period
                        </td>
                      </tr>
                    ) : (
                      therapistStats.map((therapist) => (
                        <tr key={therapist.therapist_id} data-testid={`therapist-row-${therapist.therapist_id}`}>
                          <td className="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap">
                            <div className="text-xs md:text-sm font-medium text-gray-900">
                              {therapist.therapist_name}
                            </div>
                          </td>
                          <td className="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap">
                            <div className="text-xs md:text-sm text-gray-900">
                              {therapist.total_hours.toFixed(1)}h
                            </div>
                          </td>
                          <td className="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap">
                            <div className="text-xs md:text-sm text-gray-900">
                              {therapist.total_revenue.toLocaleString()} RSD
                            </div>
                          </td>
                          <td className="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap">
                            <div className="text-xs md:text-sm text-gray-900">{therapist.client_count}</div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
