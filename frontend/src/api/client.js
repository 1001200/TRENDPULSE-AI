import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

// JWT interceptor — attach token to every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('tp_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — handle unauthorized responses gracefully
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const url = err.config?.url || ''
      const isAuthCheck = url.includes('/auth/me') ||
        url.includes('/auth/login') ||
        url.includes('/auth/register') ||
        url.includes('/auth/forgot-password') ||
        url.includes('/auth/reset-password')
      const isPublic = url.includes('/public/') || url.includes('/analyst/')

      if (!isAuthCheck && !isPublic) {
        localStorage.removeItem('tp_token')
        // Dispatch custom event so AuthContext handles logout cleanly
        window.dispatchEvent(new Event('tp_auth_unauthorized'))
      }
    }
    return Promise.reject(err)
  }
)

// ── Auth ─────────────────────────────────────────────────────────
export const authAPI = {
  register: (email, password) =>
    api.post('/auth/register', { email, password }),
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  googleLogin: (credential) =>
    api.post('/auth/google/verify-token', { credential }),
  googleAuthorizeUrl: '/api/v1/auth/google/authorize',
  logout: () =>
    api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  forgotPassword: (email) =>
    api.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) =>
    api.post('/auth/reset-password', { token, new_password: newPassword }),
  verifyEmail: (token) =>
    api.post('/auth/verify-email', { token }),
}

// ── Seller Business Profile ──────────────────────────────────────
export const businessAPI = {
  getProfile: () => api.get('/business/profile'),
  setupProfile: (data) => api.post('/business/profile', data),
  getDashboard: () => api.get('/business/dashboard'),
}

// ── Datasets ─────────────────────────────────────────────────────
export const datasetAPI = {
  upload: (file, onProgress) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/datasets/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    })
  },
  list: () => api.get('/datasets/'),
  get: (id) => api.get(`/datasets/${id}`),
  getResult: (id) => api.get(`/datasets/${id}/result`),
  delete: (id) => api.delete(`/datasets/${id}`),
}

// ── Analytics ────────────────────────────────────────────────────
export const analyticsAPI = {
  overview: (id) => api.get(`/analytics/${id}/overview`),
  periodComparison: (id) => api.get(`/analytics/${id}/period-comparison`),
  customers: (id) => api.get(`/analytics/${id}/customers`),
  timeSeries: (id) => api.get(`/analytics/${id}/time-series`),
  revenueDecomposition: (id) => api.get(`/analytics/${id}/revenue-decomposition`),
  performanceDrivers: (id) => api.get(`/analytics/${id}/performance-drivers`),
  productAffinity: (id) => api.get(`/analytics/${id}/product-affinity`),
}

// ── Apparel ──────────────────────────────────────────────────────
export const apparelAPI = {
  sizeCurves: (id) => api.get(`/apparel/${id}/size-curves`),
  colorways: (id) => api.get(`/apparel/${id}/colorways`),
  intelligence: (id) => api.get(`/apparel/${id}/intelligence`),
}

// ── Social & Curation ────────────────────────────────────────────
export const socialAPI = {
  aestheticVelocity: (id) => api.get(`/social/${id}/aesthetic-velocity`),
  dropVelocity: (id) => api.get(`/social/${id}/drop-velocity`),
  sourcing: (id) => api.get(`/social/${id}/sourcing`),
}

// ── Economics ────────────────────────────────────────────────────
export const economicsAPI = {
  unitEconomics: (id) => api.get(`/economics/${id}/unit-economics`),
  inventoryHealth: (id) => api.get(`/economics/${id}/inventory-health`),
}

// ── ML Intelligence ──────────────────────────────────────────────
export const mlAPI = {
  summary: (id) => api.get(`/ml/${id}/summary`),
  demandForecast: (id) => api.get(`/ml/${id}/demand-forecast`),
  productLifecycle: (id) => api.get(`/ml/${id}/product-lifecycle`),
  stockoutPredictions: (id) => api.get(`/ml/${id}/stockout-predictions`),
  priceElasticity: (id) => api.get(`/ml/${id}/price-elasticity`),
  simulatePrice: (id, product, newPrice) =>
    api.post(`/ml/${id}/simulate-price`, { product, new_price: newPrice }),
  customerPredictions: (id) => api.get(`/ml/${id}/customer-predictions`),
  decisionCenter: (id) => api.get(`/ml/${id}/decision-center`),
  modelRegistry: (id) => api.get(`/ml/${id}/model-registry`),
}

// ── AI Fashion Advisor & Copilot ─────────────────────────────────
export const aiAPI = {
  diagnosis: (id) => api.get(`/ai/diagnosis/${id}`),
  chat: (id, query) => api.post(`/ai/chat/${id}`, { query }),
}

// ── Export ────────────────────────────────────────────────────────
export const exportAPI = {
  cleanCSV: (id) => api.get(`/export/${id}/clean-csv`, { responseType: 'blob' }),
  reportJSON: (id) => api.get(`/export/${id}/report-json`, { responseType: 'blob' }),
}

// ── Public Instagram Drop API (No Auth) ───────────────
export const dropPublicAPI = {
  getDrop: (slug) => api.get(`/public/drop/${slug}`),
  claimItem: (itemId, buyerPhone) =>
    api.post(`/public/items/${itemId}/claim`, { buyer_phone: buyerPhone }),
  checkout: (itemId, data) =>
    api.post(`/public/items/${itemId}/checkout`, data),
}

// ── Seller Drop & Operations API ───────────────────────
export const dropSellerAPI = {
  getStore: () => api.get('/seller/store'),
  updateStore: (data) => api.post('/seller/store', data),
  getDrops: () => api.get('/seller/drops'),
  createDrop: (title, slug) => api.post('/seller/drops', { title, slug }),
  updateDropStatus: (dropId, status) => api.patch(`/seller/drops/${dropId}/status`, { status }),
  addItem: (dropId, itemData) => api.post(`/seller/drops/${dropId}/items`, itemData),
  deleteItem: (dropId, itemId) => api.delete(`/seller/drops/${dropId}/items/${itemId}`),
  uploadImage: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/seller/upload-image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getOrders: () => api.get('/seller/orders'),
  verifyOrder: (orderId) => api.post(`/seller/orders/${orderId}/verify`),
  exportShiprocketCSV: () => api.get('/seller/export/shiprocket', { responseType: 'blob' }),
  getSourcingCard: () => api.get('/seller/sourcing-card'),
}

// ── AutoAnalyst Engine API ─────────────────────────────
export const analystAPI = {
  analyzeFile: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyst/analyze', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  analyzeSample: (sampleId) => api.post(`/analyst/analyze?sample_id=${sampleId}`),
  downloadCleanedUrl: (analysisId) => `/api/v1/analyst/download-cleaned/${analysisId}`,
}

export default api
