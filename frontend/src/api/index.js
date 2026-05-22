import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

// Restore token from localStorage on page load
const token = localStorage.getItem('netops_token')
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

export { api }

export const deviceApi = {
  list: (params) => api.get('/devices', { params }),
  get: (id) => api.get(`/devices/${id}`),
  create: (data) => api.post('/devices', data),
  update: (id, data) => api.put(`/devices/${id}`, data),
  delete: (id) => api.delete(`/devices/${id}`),
}

export const credentialApi = {
  list: (params) => api.get('/credentials', { params }),
  get: (id) => api.get(`/credentials/${id}`),
  create: (data) => api.post('/credentials', data),
  update: (id, data) => api.put(`/credentials/${id}`, data),
  delete: (id) => api.delete(`/credentials/${id}`),
}

export const configApi = {
  list: (deviceId) => api.get(`/configs/${deviceId}`),
  diff: (deviceId, from, to) => api.get(`/configs/${deviceId}/diff`, { params: { from_version: from, to_version: to } }),
}

export const monitorApi = {
  metrics: (deviceId, type, hours) => api.get(`/monitor/${deviceId}`, { params: { metric_type: type, hours } }),
  latest: (deviceId) => api.get(`/monitor/${deviceId}/latest`),
}

export const taskApi = {
  list: (params) => api.get('/tasks', { params }),
  get: (id) => api.get(`/tasks/${id}`),
  create: (data) => api.post('/tasks', data),
}

export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
  deviceTypes: () => api.get('/dashboard/device-types'),
  recentTasks: () => api.get('/dashboard/recent-tasks'),
}
