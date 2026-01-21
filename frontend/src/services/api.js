import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Camera API
export const cameraAPI = {
    getAll: () => api.get('/cameras'),
    getById: (id) => api.get(`/cameras/${id}`),
    create: (data) => api.post('/cameras', data),
    update: (id, data) => api.put(`/cameras/${id}`, data),
    delete: (id) => api.delete(`/cameras/${id}`),
};

// Zone API
export const zoneAPI = {
    getAll: (cameraId) => api.get('/zones', { params: { camera_id: cameraId } }),
    create: (data) => api.post('/zones', data),
    update: (id, data) => api.put(`/zones/${id}`, data),
    delete: (id) => api.delete(`/zones/${id}`),
};

// Event API
export const eventAPI = {
    getAll: (params) => api.get('/events', { params }),
    getById: (id) => api.get(`/events/${id}`),
    getStats: (params) => api.get('/events/stats', { params }),
};

// System API
export const systemAPI = {
    health: () => api.get('/health'),
    metrics: () => api.get('/metrics'),
};

export default api;
