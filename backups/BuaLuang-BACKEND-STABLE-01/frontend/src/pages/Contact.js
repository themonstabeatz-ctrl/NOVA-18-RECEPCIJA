import React, { useState, useEffect } from 'react';
import { serviceService } from '../services/api';

const Contact = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    client_first_name: '',
    client_last_name: '',
    client_phone: '',
    client_email: '',
    service_id: '',
    preferred_date: '',
    preferred_time: '',
    message: ''
  });

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      const response = await serviceService.getAll();
      setServices(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching services:', error);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Find selected service for snapshot prices
    const selectedService = services.find(s => s.id === formData.service_id);
    
    if (!selectedService) {
      alert('Molimo vas da izaberete uslugu');
      return;
    }

    const bookingPayload = {
      ...formData,
      start_time: `${formData.preferred_date}T${formData.preferred_time}:00`,
      therapist_id: 'placeholder', // This would need to be selected or assigned
      // Snapshot prices for accurate record keeping
      snapshot_original_price: selectedService.price,
      snapshot_price: selectedService.final_price,
      snapshot_discount_percentage: selectedService.discount_percentage
    };

    try {
      // Get therapist ID (use first available or generic therapist)
      const therapistsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/therapists`);
      const therapists = await therapistsResponse.json();
      const therapist = therapists.find(t => t.name === 'Web Rezervacije (Generic)') || therapists[0];
      
      if (!therapist) {
        alert('Nema dostupnih terapeuta. Molimo kontaktirajte recepciju.');
        return;
      }
      
      // Update payload with therapist
      bookingPayload.therapist_id = therapist.id;
      
      // Call booking API
      console.log('Booking payload:', bookingPayload);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/appointments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(bookingPayload)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Booking failed');
      }
      
      const result = await response.json();
      console.log('Booking successful:', result);
      alert(`Rezervacija uspešno kreirana! Booking ID: ${result.id}`);
      
      // Reset form
      setFormData({
        client_first_name: '',
        client_last_name: '',
        client_phone: '',
        client_email: '',
        service_id: '',
        preferred_date: '',
        preferred_time: '',
        message: ''
      });
    } catch (error) {
      console.error('Booking error:', error);
      alert(`Greška pri kreiranju rezervacije: ${error.message}`);
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

  const renderServiceOption = (service) => {
    const hasDiscount = service.discount_percentage > 0;
    
    if (hasDiscount) {
      return (
        <option key={service.id} value={service.id}>
          {service.name} - {service.duration} min - {formatCurrency(service.price)} → {formatCurrency(service.final_price)} (-{service.discount_percentage}%)
        </option>
      );
    }
    
    return (
      <option key={service.id} value={service.id}>
        {service.name} - {service.duration} min - {formatCurrency(service.price)}
      </option>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-amber-400 mb-4">BOOKING</h1>
            <p className="text-gray-400">Zakažite svoj tretman</p>
          </div>

          <div className="bg-gray-800 rounded-lg p-8 shadow-xl">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-amber-400 mb-2">Ime</label>
                  <input
                    type="text"
                    value={formData.client_first_name}
                    onChange={(e) => setFormData({...formData, client_first_name: e.target.value})}
                    className="w-full px-4 py-2 bg-gray-700 border border-amber-600 rounded text-white focus:outline-none focus:border-amber-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-amber-400 mb-2">Prezime</label>
                  <input
                    type="text"
                    value={formData.client_last_name}
                    onChange={(e) => setFormData({...formData, client_last_name: e.target.value})}
                    className="w-full px-4 py-2 bg-gray-700 border border-amber-600 rounded text-white focus:outline-none focus:border-amber-400"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-amber-400 mb-2">Telefon</label>
                  <input
                    type="tel"
                    value={formData.client_phone}
                    onChange={(e) => setFormData({...formData, client_phone: e.target.value})}
                    className="w-full px-4 py-2 bg-gray-700 border border-amber-600 rounded text-white focus:outline-none focus:border-amber-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-amber-400 mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.client_email}
                    onChange={(e) => setFormData({...formData, client_email: e.target.value})}
                    className="w-full px-4 py-2 bg-gray-700 border border-amber-600 rounded text-white focus:outline-none focus:border-amber-400"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-amber-400 mb-2">
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
                      </svg>
                      Željeni datum
                    </span>
                  </label>
                  <input
                    type="date"
                    value={formData.preferred_date}
                    onChange={(e) => setFormData({...formData, preferred_date: e.target.value})}
                    className="w-full px-4 py-2 bg-gray-700 border border-amber-600 rounded text-white focus:outline-none focus:border-amber-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-amber-400 mb-2">
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd"/>
                      </svg>
                      Željeno vreme
                    </span>
                  </label>
                  <input
                    type="time"
                    value={formData.preferred_time}
                    onChange={(e) => setFormData({...formData, preferred_time: e.target.value})}
                    className="w-full px-4 py-2 bg-gray-700 border border-amber-600 rounded text-white focus:outline-none focus:border-amber-400"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-amber-400 mb-2">Izaberite uslugu</label>
                <select
                  value={formData.service_id}
                  onChange={(e) => setFormData({...formData, service_id: e.target.value})}
                  className="w-full px-4 py-2 bg-gray-700 border border-amber-600 rounded text-white focus:outline-none focus:border-amber-400"
                  required
                >
                  <option value="">-- Odaberite uslugu --</option>
                  {loading ? (
                    <option disabled>Učitavanje usluga...</option>
                  ) : (
                    services.map(renderServiceOption)
                  )}
                </select>
                
                {formData.service_id && (() => {
                  const selectedService = services.find(s => s.id === formData.service_id);
                  if (selectedService && selectedService.discount_percentage > 0) {
                    return (
                      <div className="mt-3 p-4 bg-green-900/30 border border-green-600 rounded">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-400 text-sm line-through">
                              Originalna cena: {formatCurrency(selectedService.price)}
                            </p>
                            <p className="text-green-400 text-lg font-bold">
                              Cena sa popustom: {formatCurrency(selectedService.final_price)}
                            </p>
                          </div>
                          <div className="bg-red-600 text-white px-4 py-2 rounded-full font-bold">
                            -{selectedService.discount_percentage}%
                          </div>
                        </div>
                        <p className="text-green-400 text-sm mt-2">
                          ✨ Ušteda: {formatCurrency(selectedService.price - selectedService.final_price)}
                        </p>
                      </div>
                    );
                  }
                  return null;
                })()}
              </div>

              <div>
                <label className="block text-amber-400 mb-2">Poruka</label>
                <textarea
                  value={formData.message}
                  onChange={(e) => setFormData({...formData, message: e.target.value})}
                  rows="4"
                  className="w-full px-4 py-2 bg-gray-700 border border-amber-600 rounded text-white focus:outline-none focus:border-amber-400"
                  placeholder="Opišite kako možemo da vam pomognemo..."
                />
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-black font-bold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105"
              >
                ✈️ Pošaljite
              </button>
            </form>
          </div>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-amber-400 font-bold mb-2">Otkazivanje</h3>
              <p className="text-gray-400 text-sm">Molimo vas da otkazujete termine najmanje 4 sata unapred</p>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-amber-400 font-bold mb-2">Kašnjenje</h3>
              <p className="text-gray-400 text-sm">Kašnjenje duže od 15 minuta može rezultovati skraćivanjem tretmana</p>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-amber-400 font-bold mb-2">Grupne rezervacije</h3>
              <p className="text-gray-400 text-sm">Za grupe veće od 4 osobe, molimo vas da nas kontaktirate direktno</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact;
