import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'https://209.38.79.211'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export const adminAPI = {
  // Auth
  login: (username, password) =>
    api.post('/api/admin/login', { username, password }),

  // Dashboard
  getDashboard: () => api.get('/api/admin/dashboard'),

  // Users
  getUsers: () => api.get('/api/admin/users'),
  createUser: (data) => api.post('/api/admin/users', data),
  updateUser: (id, data) => api.put(`/api/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/api/admin/users/${id}`),

  // Licenses
  getLicenses: () => api.get('/api/admin/licenses'),
  createLicense: (data) => api.post('/api/admin/licenses', data),
  updateLicense: (id, isActive) =>
    api.put(`/api/admin/licenses/${id}?is_active=${isActive}`),
  deleteLicense: (id) => api.delete(`/api/admin/licenses/${id}`)
}

export default api
