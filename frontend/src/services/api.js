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
};

export default api;
