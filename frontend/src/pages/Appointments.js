import React, { useState, useEffect } from 'react';
import { appointmentService, therapistService, serviceService } from '../services/api';
import { Plus, Edit2, Trash2, X, Calendar as CalendarIcon, Check } from 'lucide-react';

const Appointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [therapists, setTherapists] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [formData, setFormData] = useState({
    client_first_name: '',
    client_last_name: '',
    client_phone: '',
    client_email: '',
    therapist_id: '',
    service_id: '',
    start_time: '',
    status: 'scheduled',
  });

  useEffect(() => {
    fetchData();
  }, [selectedDate]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const startOfDay = `${selectedDate}T00:00:00`;
      const endOfDay = `${selectedDate}T23:59:59`;

      const [appointmentsRes, therapistsRes, servicesRes] = await Promise.all([
        appointmentService.getAll({ start_date: startOfDay, end_date: endOfDay }),
        therapistService.getAll(true),
        serviceService.getAll(),
      ]);

      setAppointments(appointmentsRes.data);
      setTherapists(therapistsRes.data);
      setServices(servicesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        start_time: new Date(formData.start_time).toISOString(),
      };

      if (editingAppointment) {
        await appointmentService.update(editingAppointment.id, data);
      } else {
        await appointmentService.create(data);
      }
      fetchData();
      handleCloseModal();
    } catch (error) {
      console.error('Error saving appointment:', error);
      const errorMsg = error.response?.data?.detail || 'Greška pri čuvanju termina';
      alert(errorMsg);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Da li ste sigurni da želite da obrišete ovaj termin?')) {
      try {
        await appointmentService.delete(id);
        fetchData();
      } catch (error) {
        console.error('Error deleting appointment:', error);
        alert('Greška pri brisanju termina');
      }
    }
  };

  const handleEdit = (appointment) => {
    setEditingAppointment(appointment);
    // Convert ISO string to datetime-local format
    const startTime = new Date(appointment.start_time);
    const localDateTime = new Date(startTime.getTime() - startTime.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);

    setFormData({
      client_first_name: appointment.client_first_name,
      client_last_name: appointment.client_last_name,
      client_phone: appointment.client_phone,
      client_email: appointment.client_email || '',
      therapist_id: appointment.therapist_id,
      service_id: appointment.service_id,
      start_time: localDateTime,
      status: appointment.status,
    });
    setShowModal(true);
  };

  const handleCompleteAppointment = async (id) => {
    try {
      await appointmentService.updateStatus(id, 'completed');
      fetchData();
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Greška pri ažuriranju statusa');
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingAppointment(null);
    setFormData({
      client_first_name: '',
      client_last_name: '',
      client_phone: '',
      client_email: '',
      therapist_id: '',
      service_id: '',
      start_time: '',
      status: 'scheduled',
    });
  };

  const getTherapistName = (id) => {
    const therapist = therapists.find((t) => t.id === id);
    return therapist?.name || 'Unknown';
  };

  const getServiceName = (id) => {
    const service = services.find((s) => s.id === id);
    return service?.name || 'Unknown';
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('sr-RS', { hour: '2-digit', minute: '2-digit' });
  };

  const statusLabels = {
    scheduled: 'Zakazan',
    completed: 'Završen',
    cancelled: 'Otkazan',
  };

  const statusColors = {
    scheduled: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8" data-testid="appointments-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900" data-testid="appointments-title">
              Termini
            </h1>
            <p className="mt-2 text-gray-600">Upravljanje terminima i zakazivanjima</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            data-testid="add-appointment-btn"
          >
            <Plus className="w-5 h-5 mr-2" />
            Zakazite termin
          </button>
        </div>

        {/* Date Picker */}
        <div className="mb-6 flex items-center gap-4">
          <CalendarIcon className="w-5 h-5 text-gray-500" />
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="date-picker"
          />
        </div>

        {loading ? (
          <div className="text-center py-12" data-testid="appointments-loading">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Vreme
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Klijent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Kontakt
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usluga
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Terapeut
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Akcije
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {appointments.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                      Nema zakazanih termina za ovaj dan.
                    </td>
                  </tr>
                ) : (
                  appointments.map((appointment) => (
                    <tr key={appointment.id} data-testid={`appointment-row-${appointment.id}`}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {formatTime(appointment.start_time)} - {formatTime(appointment.end_time)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {appointment.client_first_name} {appointment.client_last_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{appointment.client_phone}</div>
                        {appointment.client_email && (
                          <div className="text-xs text-gray-500">{appointment.client_email}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {getServiceName(appointment.service_id)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {getTherapistName(appointment.therapist_id)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            statusColors[appointment.status]
                          }`}
                        >
                          {statusLabels[appointment.status]}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {appointment.status === 'scheduled' && (
                          <button
                            onClick={() => handleCompleteAppointment(appointment.id)}
                            className="text-green-600 hover:text-green-900 mr-4"
                            data-testid={`complete-appointment-${appointment.id}`}
                            title="Označi kao završeno"
                          >
                            <Check className="w-5 h-5" />
                          </button>
                        )}
                        <button
                          onClick={() => handleEdit(appointment)}
                          className="text-indigo-600 hover:text-indigo-900 mr-4"
                          data-testid={`edit-appointment-${appointment.id}`}
                        >
                          <Edit2 className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleDelete(appointment.id)}
                          className="text-red-600 hover:text-red-900"
                          data-testid={`delete-appointment-${appointment.id}`}
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          data-testid="appointment-modal"
        >
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingAppointment ? 'Izmeni termin' : 'Zakazite termin'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600"
                data-testid="close-modal-btn"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} data-testid="appointment-form">
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ime *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.client_first_name}
                      onChange={(e) =>
                        setFormData({ ...formData, client_first_name: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="client-firstname-input"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prezime *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.client_last_name}
                      onChange={(e) =>
                        setFormData({ ...formData, client_last_name: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="client-lastname-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Telefon *
                    </label>
                    <input
                      type="tel"
                      required
                      value={formData.client_phone}
                      onChange={(e) =>
                        setFormData({ ...formData, client_phone: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="client-phone-input"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      value={formData.client_email}
                      onChange={(e) =>
                        setFormData({ ...formData, client_email: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="client-email-input"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Usluga *
                  </label>
                  <select
                    required
                    value={formData.service_id}
                    onChange={(e) => setFormData({ ...formData, service_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="service-select"
                  >
                    <option value="">Izaberite uslugu</option>
                    {services.map((service) => (
                      <option key={service.id} value={service.id}>
                        {service.name} - {service.duration} min - {service.price} RSD
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Terapeut *
                  </label>
                  <select
                    required
                    value={formData.therapist_id}
                    onChange={(e) => setFormData({ ...formData, therapist_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="therapist-select"
                  >
                    <option value="">Izaberite terapeuta</option>
                    {therapists.map((therapist) => (
                      <option key={therapist.id} value={therapist.id}>
                        {therapist.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Datum i vreme početka *
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="start-time-input"
                  />
                </div>

                {editingAppointment && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="status-select"
                    >
                      <option value="scheduled">Zakazan</option>
                      <option value="completed">Završen</option>
                      <option value="cancelled">Otkazan</option>
                    </select>
                  </div>
                )}
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
                  data-testid="save-appointment-btn"
                >
                  Sačuvaj
                </button>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
                  data-testid="cancel-appointment-btn"
                >
                  Otkaži
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Appointments;
