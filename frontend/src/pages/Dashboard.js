import React, { useState, useEffect } from 'react';
import { analyticsService } from '../services/api';
import { TrendingUp, Users, DollarSign, Clock } from 'lucide-react';

const Dashboard = () => {
  const [period, setPeriod] = useState('week');
  const [therapistStats, setTherapistStats] = useState([]);
  const [revenueData, setRevenueData] = useState(null);
  const [clientData, setClientData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [period]);

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

  return (
    <div className="min-h-screen bg-gray-50 py-8" data-testid="dashboard-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900" data-testid="dashboard-title">CEO Dashboard</h1>
          <p className="mt-2 text-gray-600">Pregled performansi i statistike</p>
        </div>

        {/* Period Selector */}
        <div className="mb-6 flex gap-2" data-testid="period-selector">
          {Object.entries(periodLabels).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setPeriod(key)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
            <div className="bg-white rounded-lg shadow" data-testid="therapist-stats-table">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Statistike po terapeutu</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Terapeut
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Radni sati
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Zarada
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Broj klijenata
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {therapistStats.length === 0 ? (
                      <tr>
                        <td colSpan="4" className="px-6 py-4 text-center text-gray-500">
                          Nema podataka za izabrani period
                        </td>
                      </tr>
                    ) : (
                      therapistStats.map((therapist) => (
                        <tr key={therapist.therapist_id} data-testid={`therapist-row-${therapist.therapist_id}`}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {therapist.therapist_name}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {therapist.total_hours.toFixed(1)}h
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {therapist.total_revenue.toLocaleString()} RSD
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{therapist.client_count}</div>
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
    </div>
  );
};

export default Dashboard;
