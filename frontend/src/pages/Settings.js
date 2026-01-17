import React, { useState, useEffect } from 'react';
import { businessHoursService } from '../services/api';
import { Clock, Save } from 'lucide-react';

const Settings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    start_time: '10:00',
    end_time: '22:00',
    slot_duration: 30,
  });

  useEffect(() => {
    fetchBusinessHours();
  }, []);

  const fetchBusinessHours = async () => {
    setLoading(true);
    try {
      const response = await businessHoursService.get();
      setFormData({
        start_time: response.data.start_time,
        end_time: response.data.end_time,
        slot_duration: response.data.slot_duration,
      });
    } catch (error) {
      console.error('Error fetching business hours:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await businessHoursService.update(formData);
      alert('Podešavanja su uspešno sačuvana!');
    } catch (error) {
      console.error('Error updating business hours:', error);
      alert('Greška pri čuvanju podešavanja');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-4 md:py-8" data-testid="settings-page">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900" data-testid="settings-title">
            Podešavanja
          </h1>
          <p className="mt-2 text-gray-600">Konfigurišite radno vreme i intervale</p>
        </div>

        {loading ? (
          <div className="text-center py-12" data-testid="settings-loading">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="flex items-center mb-6">
              <Clock className="w-6 h-6 text-indigo-600 mr-3" />
              <h2 className="text-xl font-semibold text-gray-900">Radno vreme</h2>
            </div>

            <form onSubmit={handleSubmit} data-testid="settings-form">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Početak radnog vremena
                  </label>
                  <input
                    type="time"
                    required
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="start-time-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Kraj radnog vremena
                  </label>
                  <input
                    type="time"
                    required
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="end-time-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Interval slotova (minuta)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="1440"
                    value={formData.slot_duration}
                    onChange={(e) =>
                      setFormData({ ...formData, slot_duration: parseInt(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="slot-duration-input"
                    placeholder="Unesite broj minuta (npr. 5, 10, 15, 30...)"
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Unesite bilo koji broj minuta od 1 do 1440 (24 sata)
                  </p>
                </div>

                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={saving}
                    className="w-full inline-flex justify-center items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    data-testid="save-settings-btn"
                  >
                    <Save className="w-5 h-5 mr-2" />
                    {saving ? 'Snimanje...' : 'Sačuvaj podešavanja'}
                  </button>
                </div>
              </div>
            </form>

            <div className="mt-8 pt-8 border-t border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Informacije</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <p>
                  <strong>Radno vreme:</strong> {formData.start_time} - {formData.end_time}
                </p>
                <p>
                  <strong>Trajanje slota:</strong> {formData.slot_duration} minuta
                </p>
                <p className="mt-4 text-xs text-gray-500">
                  Napomena: Ova podešavanja utiču na korišćenje kalendara i zakazivanje termina.
                  Termini se mogu zakazivati samo u okviru definisanog radnog vremena.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Settings;
