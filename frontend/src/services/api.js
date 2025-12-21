import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Therapists
export const therapistService = {
  getAll: (activeOnly = false) => api.get(`/therapists?active_only=${activeOnly}`),
  getOne: (id) => api.get(`/therapists/${id}`),
  create: (data) => api.post('/therapists', data),
  update: (id, data) => api.put(`/therapists/${id}`, data),
  delete: (id) => api.delete(`/therapists/${id}`),
  getAvailability: (date) => api.get(`/therapists/availability/status?date=${date}`),
};

// Services
export const serviceService = {
  getAll: () => api.get('/services'),
  getOne: (id) => api.get(`/services/${id}`),
  create: (data) => api.post('/services', data),
  update: (id, data) => api.put(`/services/${id}`, data),
  delete: (id) => api.delete(`/services/${id}`),
  updateDiscount: (id, discount) => api.patch(`/services/${id}/discount?discount=${discount}`),
};

// Appointments
export const appointmentService = {
  getAll: (params) => api.get('/appointments', { params }),
  getOne: (id) => api.get(`/appointments/${id}`),
  create: (data) => api.post('/appointments', data),
  update: (id, data) => api.put(`/appointments/${id}`, data),
  delete: (id) => api.delete(`/appointments/${id}`),
  updateStatus: (id, status) => api.patch(`/appointments/${id}/status?status=${status}`),
  getUnviewedCount: () => api.get('/appointments/unviewed/count'),
  getUnviewedList: () => api.get('/appointments/unviewed/list'),
  markViewed: (id) => api.patch(`/appointments/${id}/mark-viewed`),
  markAllViewed: () => api.patch('/appointments/mark-all-viewed'),
};

// Business Hours
export const businessHoursService = {
  get: () => api.get('/business-hours'),
  update: (data) => api.put('/business-hours', data),
};

// Analytics
export const analyticsService = {
  getTherapistStats: (params) => api.get('/analytics/therapist-stats', { params }),
  getRevenue: (params) => api.get('/analytics/revenue', { params }),
  getClients: (params) => api.get('/analytics/clients', { params }),
  getDetailed: (params) => api.get('/analytics/detailed', { params }),
};

// SPA Services
export const spaService = {
  // Get all SPA services
  getServices: () => api.get('/spa/services'),
  
  // Get SPA cards with discounts
  getCards: () => api.get('/spa/cards'),
  
  // Update card discount
  updateCardDiscount: (cardId, discount) => 
    api.patch(`/spa/cards/${cardId}/discount?discount=${discount}`),
  
  // Get quote for SPA booking
  getQuote: (data) => api.post('/spa/quote', data),
  
  // Get card-level quote
  getCardQuote: (data) => api.post('/spa/card-quote', data),
  
  // Create SPA appointment
  createAppointment: (data) => api.post('/spa/appointments', data),
};

/**
 * Fetch SPA quote with card discount
 * @param {string[]} serviceIds - Array of service IDs
 * @param {string} cardId - Card ID for discount lookup
 * @param {object} options - Additional options (spa_category, selected_zones, etc.)
 */
export async function fetchSpaQuote(serviceIds, cardId, options = {}) {
  try {
    const payload = {
      service_ids: serviceIds || [],
      card_id: cardId,
      ...options
    };
    
    console.log('📊 SPA Quote Request:', payload);
    
    const response = await api.post('/spa/quote', payload);
    
    console.log('📊 SPA Quote Response:', response.data);
    
    return response.data;
  } catch (error) {
    console.error('SPA Quote Error:', error);
    return null;
  }
}

export default api;
