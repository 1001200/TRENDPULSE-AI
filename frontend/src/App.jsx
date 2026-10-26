import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'

import OverviewPage from './pages/OverviewPage'
import SalesPerformancePage from './pages/SalesPerformancePage'
import ProductsPage from './pages/ProductsPage'
import SizesPricingPage from './pages/SizesPricingPage'
import CustomersPage from './pages/CustomersPage'
import TrendsPage from './pages/TrendsPage'
import UploadPage from './pages/UploadPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/sales" element={<SalesPerformancePage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/sizes-pricing" element={<SizesPricingPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/trends" element={<TrendsPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
