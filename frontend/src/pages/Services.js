import React, { useState, useEffect } from 'react';
import { serviceService } from '../services/api';
import { Plus, Edit2, Trash2, X } from 'lucide-react';

// API base URL for SPA services (separate from massage services)
const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// Updated with new duration options: 15, 165, 195, 225, 255
const Services = () => {
  const [services, setServices] = useState([]);
  const [spaServices, setSpaServices] = useState([]); // SPA services (separate)
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [activeCategory, setActiveCategory] = useState('Obicne masaze');
  const [formData, setFormData] = useState({
    name: '',
    duration: 60,
    price: '',
    description: '',
  });

  const categories = [
    { id: 'Obicne masaze', label: 'Obicne masaze' },
    { id: 'Kartica Masaza za parove', label: 'Kartica Masaza za parove' },
    { id: 'SPA', label: 'SPA' },
    { id: 'SPA paketi za posebne prilike', label: 'SPA paketi za posebne prilike' },
    { id: 'SPA ZONE', label: 'SPA ZONE' }  // Renamed from "SPA add-ons (doplate)"
  ];

  const durationOptions = [
    { value: 15, label: '15 minuta' },
    { value: 30, label: '30 minuta' },
    { value: 45, label: '45 minuta' },
    { value: 60, label: '60 minuta (1h)' },
    { value: 90, label: '90 minuta (1.5h)' },
    { value: 120, label: '120 minuta (2h)' },
    { value: 150, label: '150 minuta (2.5h)' },
    { value: 165, label: '165 minuta (2h 45min)' },
    { value: 180, label: '180 minuta (3h)' },
    { value: 195, label: '195 minuta (3h 15min)' },
    { value: 210, label: '210 minuta (3.5h)' },
    { value: 225, label: '225 minuta (3h 45min)' },
    { value: 240, label: '240 minuta (4h)' },
    { value: 255, label: '255 minuta (4h 15min)' },
    { value: 270, label: '270 minuta (4h 30min)' },
    { value: 285, label: '285 minuta (4h 45min)' },
    { value: 300, label: '300 minuta (5h)' },
    { value: 315, label: '315 minuta (5h 15min)' },
    { value: 330, label: '330 minuta (5h 30min)' },
    { value: 360, label: '360 minuta (6h)' },
    { value: 420, label: '420 minuta (7h)' },
  ];

  useEffect(() => {
    fetchServices();
    fetchSpaServices(); // Also load SPA services
  }, []);

  const fetchServices = async () => {
    setLoading(true);
    try {
      const response = await serviceService.getAll();
      setServices(response.data);
    } catch (error) {
      console.error('Error fetching services:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch SPA services from separate endpoint
  const fetchSpaServices = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/spa/services`, { credentials: 'include' });
      if (!res.ok) throw new Error(`SPA services load failed: ${res.status}`);
      const data = await res.json();
      setSpaServices(data);
      console.log('SPA services loaded:', data.length);
    } catch (error) {
      console.error('Error fetching SPA services:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        price: parseFloat(formData.price),
        duration: parseInt(formData.duration),
        // Add required fields for backend
        category: activeCategory,
        service_code: formData.name, // Use service name as service_code
        is_couple: activeCategory === 'Kartica Masaza za parove',
        discount_percentage: formData.discount_percentage || 0,
      };

      if (editingService) {
        await serviceService.update(editingService.id, data);
      } else {
        await serviceService.create(data);
      }
      fetchServices();
      handleCloseModal();
    } catch (error) {
      console.error('Error saving service:', error);
      alert('Greška pri čuvanju usluge');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Da li ste sigurni da želite da obrišete ovu uslugu?')) {
      try {
        await serviceService.delete(id);
        fetchServices();
      } catch (error) {
        console.error('Error deleting service:', error);
        alert('Greška pri brisanju usluge');
      }
    }
  };

  // Check if current category is SPA
  const isSpaCategory = (category) => {
    return category === 'SPA' || category === 'SPA paketi za posebne prilike' || category === 'SPA ZONE';
  };

  const handleDiscountChange = async (serviceId, discount) => {
    try {
      // Use different endpoint for SPA services
      if (isSpaCategory(activeCategory)) {
        // SPA services use /api/spa/services/{id}/discount
        const res = await fetch(`${API_BASE}/api/spa/services/${serviceId}/discount?discount=${discount}`, {
          method: 'PATCH',
          credentials: 'include'
        });
        if (!res.ok) throw new Error(`SPA discount update failed: ${res.status}`);
        fetchSpaServices(); // Refresh SPA list
      } else {
        // Massage services use /api/services/{id}/discount
        await serviceService.updateDiscount(serviceId, discount);
        fetchServices(); // Refresh massage list
      }
    } catch (error) {
      console.error('Error updating discount:', error);
      alert('Greška pri ažuriranju popusta');
    }
  };

  const handleBulkDiscountChange = async (discount) => {
    console.log('🎯 Bulk discount clicked:', discount, 'Category:', activeCategory);
    
    // Determine which services to update based on category
    let servicesToUpdate = [];
    const isSpa = isSpaCategory(activeCategory);
    
    if (isSpa) {
      // SPA services
      if (activeCategory === 'SPA') {
        servicesToUpdate = spaServices.filter(s => s.category === 'spa_zone' || s.category === 'spa_ritual');
      } else if (activeCategory === 'SPA paketi za posebne prilike') {
        servicesToUpdate = spaServices.filter(s => s.category === 'spa_special');
      } else if (activeCategory === 'SPA ZONE') {
        servicesToUpdate = spaServices.filter(s => s.category === 'spa_addon');
      }
    } else {
      servicesToUpdate = services.filter(s => s.category === activeCategory);
    }
    
    console.log('Services to update:', servicesToUpdate.length);
    
    if (servicesToUpdate.length === 0) {
      alert('Nema usluga u ovoj kategoriji za ažuriranje!');
      return;
    }
    
    if (!window.confirm(`Da li ste sigurni da želite da primenite ${discount}% popust na SVE usluge (${servicesToUpdate.length}) u kategoriji "${activeCategory}"?`)) {
      return;
    }

    try {
      console.log('Updating services...');
      
      // Update all services one by one with better error handling
      let successCount = 0;
      let errorCount = 0;
      
      for (const service of servicesToUpdate) {
        try {
          if (isSpa) {
            // SPA services use /api/spa/services/{id}/discount
            const res = await fetch(`${API_BASE}/api/spa/services/${service.id}/discount?discount=${discount}`, {
              method: 'PATCH',
              credentials: 'include'
            });
            if (!res.ok) throw new Error(`Failed: ${res.status}`);
          } else {
            await serviceService.updateDiscount(service.id, discount);
          }
          successCount++;
          console.log(`✓ Updated: ${service.name}`);
        } catch (err) {
          errorCount++;
          console.error(`✗ Failed: ${service.name}`, err);
        }
      }
      
      if (successCount > 0) {
        alert(`✅ Popust od ${discount}% primenjen na ${successCount} usluga!${errorCount > 0 ? ` (${errorCount} grešaka)` : ''}`);
        if (isSpa) {
          fetchSpaServices();
        } else {
          fetchServices();
        }
      } else {
        alert('❌ Greška: Nijedna usluga nije ažurirana!');
      }
    } catch (error) {
      console.error('Error updating bulk discount:', error);
      alert('Greška pri grupnom ažuriranju popusta: ' + error.message);
    }
  };

  const handleEdit = (service) => {
    setEditingService(service);
    setFormData({
      name: service.name,
      duration: service.duration,
      price: service.price.toString(),
      description: service.description || '',
    });
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingService(null);
    setFormData({
      name: '',
      duration: 60,
      price: '',
      description: '',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-4 md:py-8 overflow-x-hidden" data-testid="services-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900" data-testid="services-title">Usluge</h1>
            <p className="mt-2 text-gray-600">Upravljanje uslugama i cenama</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            data-testid="add-service-btn"
          >
            <Plus className="w-5 h-5 mr-2" />
            Dodaj uslugu
          </button>
        </div>

        {/* Category Filter Buttons */}
        <div className="mb-6 flex flex-wrap gap-3">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                activeCategory === category.id
                  ? 'bg-indigo-600 text-white shadow-lg'
                  : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-indigo-400'
              }`}
            >
              {category.label}
            </button>
          ))}
        </div>

        {/* Bulk Discount Button - Only for "Kartica Masaza za parove" */}
        {activeCategory === 'Kartica Masaza za parove' && (
          <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border-2 border-purple-200">
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-gray-700 font-semibold">🎯 Postavi popust za SVE masaže odjednom:</span>
              <div className="flex gap-3 flex-wrap items-center">
                {/* 0% Button stays as button */}
                <button
                  onClick={() => handleBulkDiscountChange(0)}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-all hover:scale-105 font-medium shadow-md"
                >
                  Bez popusta (0%)
                </button>

                {/* 5% Discount Badge */}
                <button
                  onClick={() => {
                    console.log('🔥 5% button clicked!');
                    handleBulkDiscountChange(5);
                  }}
                  className="cursor-pointer transition-all hover:scale-110 hover:drop-shadow-2xl bg-transparent border-0 p-0"
                  title="Primeni 5% popust na sve"
                >
                  <img 
                    src="/discount-5.png"
                    alt="5% popust"
                    className="w-12 h-12 object-contain"
                  />
                </button>

                {/* 10% Discount Badge */}
                <button
                  onClick={() => {
                    console.log('🔥 10% button clicked!');
                    handleBulkDiscountChange(10);
                  }}
                  className="cursor-pointer transition-all hover:scale-110 hover:drop-shadow-2xl bg-transparent border-0 p-0"
                  title="Primeni 10% popust na sve"
                >
                  <img 
                    src="/discount-10.png"
                    alt="10% popust"
                    className="w-12 h-12 object-contain"
                  />
                </button>

                {/* 15% Discount Badge */}
                <button
                  onClick={() => {
                    console.log('🔥 15% button clicked!');
                    handleBulkDiscountChange(15);
                  }}
                  className="cursor-pointer transition-all hover:scale-110 hover:drop-shadow-2xl bg-transparent border-0 p-0"
                  title="Primeni 15% popust na sve"
                >
                  <img 
                    src="/discount-15.png"
                    alt="15% popust"
                    className="w-12 h-12 object-contain"
                  />
                </button>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12" data-testid="services-loading">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usluga
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Akcije (Popust)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trajanje
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cena
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Akcijska Cena
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Opcije
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(() => {
                  // Determine which services to show based on active tab
                  const isSpaTab = activeCategory === 'SPA' || activeCategory === 'SPA paketi za posebne prilike' || activeCategory === 'SPA add-ons (doplate)';
                  let displayServices = [];
                  
                  if (isSpaTab) {
                    // Use SPA services from separate endpoint
                    if (activeCategory === 'SPA') {
                      displayServices = spaServices.filter(s => s.category === 'spa_zone' || s.category === 'spa_ritual');
                    } else if (activeCategory === 'SPA paketi za posebne prilike') {
                      displayServices = spaServices.filter(s => s.category === 'spa_special');
                    } else if (activeCategory === 'SPA add-ons (doplate)') {
                      displayServices = spaServices.filter(s => s.category === 'spa_addon');
                    }
                  } else {
                    // Use regular massage services
                    displayServices = services.filter(s => s.category === activeCategory);
                  }
                  
                  if (displayServices.length === 0) {
                    return (
                      <tr>
                        <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                          Nema usluga u ovoj kategoriji. Dodajte prvu uslugu.
                        </td>
                      </tr>
                    );
                  }
                  
                  return displayServices.map((service) => {
                    // SPA uses discount_percent, massage uses discount_percentage
                    const discount = service.discount_percent ?? service.discount_percentage ?? 0;
                    // CRITICAL: Always show ORIGINAL price in "Cena" column (backend sends original_price)
                    const originalPrice = service.original_price || service.metadata?.original_price || service.price;
                    // CRITICAL: Use final_price from backend - NO frontend calculation
                    const discountedPrice = service.final_price || originalPrice * (1 - discount / 100);
                    const isPozovite = service.booking_type === 'POZOVITE';
                    
                    return (
                      <tr key={service.id} data-testid={`service-row-${service.id}`} className={isPozovite ? 'bg-yellow-50' : ''}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {service.name}
                            {isPozovite && <span className="ml-2 px-2 py-1 text-xs bg-yellow-200 text-yellow-800 rounded">POZOVITE</span>}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {isPozovite ? (
                            <span className="text-sm text-gray-500">N/A</span>
                          ) : (
                          <select
                            value={discount}
                            onChange={(e) => handleDiscountChange(service.id, parseFloat(e.target.value))}
                            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          >
                            <option value="0">Bez popusta (0%)</option>
                            <option value="5">5% popust</option>
                            <option value="10">10% popust</option>
                            <option value="15">15% popust</option>
                          </select>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{service.duration} min</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {originalPrice.toLocaleString()} RSD
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {discount > 0 ? (
                            <div>
                              <div className="text-sm font-bold text-green-600">
                                {discountedPrice.toLocaleString()} RSD
                              </div>
                              <div className="text-xs text-gray-500">
                                Ušteda: {(originalPrice - discountedPrice).toLocaleString()} RSD
                              </div>
                            </div>
                          ) : (
                            <div className="text-sm text-gray-400">-</div>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => handleEdit(service)}
                            className="text-indigo-600 hover:text-indigo-900 mr-4"
                            data-testid={`edit-service-${service.id}`}
                          >
                            <Edit2 className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(service.id)}
                            className="text-red-600 hover:text-red-900"
                            data-testid={`delete-service-${service.id}`}
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </td>
                      </tr>
                    );
                  });
                })()}
              </tbody>
            </table>
          </div>
        )}

        {/* Modal za dodavanje/izmenu usluge */}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" data-testid="service-modal">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingService ? 'Izmeni uslugu' : 'Dodaj uslugu'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600"
                data-testid="close-modal-btn"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} data-testid="service-form">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Naziv usluge *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="service-name-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trajanje *
                  </label>
                  <select
                    required
                    value={formData.duration}
                    onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="service-duration-select"
                  >
                    {durationOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cena (RSD) *
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="service-price-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Opis
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="service-description-input"
                  />
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
                  data-testid="save-service-btn"
                >
                  Sačuvaj
                </button>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
                  data-testid="cancel-service-btn"
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

export default Services;
