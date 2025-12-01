import React, { useState, useEffect } from 'react';
import { therapistService } from '../services/api';
import { Plus, Edit2, Trash2, X } from 'lucide-react';

const Therapists = () => {
  const [therapists, setTherapists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTherapist, setEditingTherapist] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    is_active: true,
  });

  useEffect(() => {
    fetchTherapists();
  }, []);

  const fetchTherapists = async () => {
    setLoading(true);
    try {
      const response = await therapistService.getAll();
      setTherapists(response.data);
    } catch (error) {
      console.error('Error fetching therapists:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingTherapist) {
        await therapistService.update(editingTherapist.id, formData);
      } else {
        await therapistService.create(formData);
      }
      fetchTherapists();
      handleCloseModal();
    } catch (error) {
      console.error('Error saving therapist:', error);
      alert('Greška pri čuvanju terapeuta');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Da li ste sigurni da želite da obrišete ovog terapeuta?')) {
      try {
        await therapistService.delete(id);
        fetchTherapists();
      } catch (error) {
        console.error('Error deleting therapist:', error);
        alert('Greška pri brisanju terapeuta');
      }
    }
  };

  const handleEdit = (therapist) => {
    setEditingTherapist(therapist);
    setFormData({
      name: therapist.name,
      phone: therapist.phone || '',
      email: therapist.email || '',
      is_active: therapist.is_active,
    });
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingTherapist(null);
    setFormData({
      name: '',
      phone: '',
      email: '',
      is_active: true,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-4 md:py-8 overflow-x-hidden" data-testid="therapists-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900" data-testid="therapists-title">Terapeuti</h1>
            <p className="mt-2 text-gray-600">Upravljanje terapeutima</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            data-testid="add-therapist-btn"
          >
            <Plus className="w-5 h-5 mr-2" />
            Dodaj terapeuta
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12" data-testid="therapists-loading">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ime
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Telefon
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
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
                {therapists.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                      Nema terapeuta. Dodajte prvog terapeuta.
                    </td>
                  </tr>
                ) : (
                  therapists.map((therapist) => (
                    <tr key={therapist.id} data-testid={`therapist-row-${therapist.id}`}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{therapist.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{therapist.phone || '-'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{therapist.email || '-'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            therapist.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {therapist.is_active ? 'Aktivan' : 'Neaktivan'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleEdit(therapist)}
                          className="text-indigo-600 hover:text-indigo-900 mr-4"
                          data-testid={`edit-therapist-${therapist.id}`}
                        >
                          <Edit2 className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleDelete(therapist.id)}
                          className="text-red-600 hover:text-red-900"
                          data-testid={`delete-therapist-${therapist.id}`}
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" data-testid="therapist-modal">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingTherapist ? 'Izmeni terapeuta' : 'Dodaj terapeuta'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600"
                data-testid="close-modal-btn"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} data-testid="therapist-form">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ime *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="therapist-name-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Telefon
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="therapist-phone-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="therapist-email-input"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    data-testid="therapist-active-checkbox"
                  />
                  <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                    Aktivan
                  </label>
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
                  data-testid="save-therapist-btn"
                >
                  Sačuvaj
                </button>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
                  data-testid="cancel-therapist-btn"
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

export default Therapists;
