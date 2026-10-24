import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { StoreProvider } from './context/StoreContext'
import { ProtectedRoute, OnboardingRoute, PublicOnlyRoute } from './components/auth/RouteGuards'
import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'
import LoginPage from './pages/LoginPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import BriefingPage from './pages/BriefingPage'
import CopilotPage from './pages/CopilotPage'
import SimulatorPage from './pages/SimulatorPage'
import InventoryPage from './pages/InventoryPage'
import EconomicsPage from './pages/EconomicsPage'
import TrendsPage from './pages/TrendsPage'
import CustomersPage from './pages/CustomersPage'
import DatasetPage from './pages/DatasetPage'
import PublicDropPage from './pages/PublicDropPage'
import QuickListerPage from './pages/QuickListerPage'
import SellerOrdersPage from './pages/SellerOrdersPage'
import LandingPage from './pages/LandingPage'
import BionisDashboardPage from './pages/BionisDashboardPage'
import AutoAnalystPage from './pages/AutoAnalystPage'
import BusinessSetupPage from './pages/BusinessSetupPage'
import SellerDashboardPage from './pages/SellerDashboardPage'

function ProtectedLayout() {
  return (
    <StoreProvider>
      <div className="app-layout">
        <Sidebar />
        <div className="main-content">
          <Header />
          <Outlet />
        </div>
      </div>
    </StoreProvider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* ── Public Landing Pages ──────────────────────────── */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/landing" element={<LandingPage />} />

          {/* ── Public Authentication Flow ────────────────────── */}
          <Route path="/login" element={<LoginPage initialMode="login" />} />
          <Route path="/signup" element={<LoginPage initialMode="register" />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />

          {/* ── One-Time Business Onboarding (Post-Auth Handoff) ── */}
          <Route
            path="/setup"
            element={
              <OnboardingRoute>
                <BusinessSetupPage />
              </OnboardingRoute>
            }
          />

          {/* ── Protected Seller Hub ──────────────────────────── */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <SellerDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="/seller" element={<Navigate to="/dashboard" replace />} />
          <Route path="/seller/setup" element={<Navigate to="/setup?edit=true" replace />} />
          <Route
            path="/seller/lister"
            element={
              <ProtectedRoute>
                <QuickListerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/seller/orders"
            element={
              <ProtectedRoute>
                <SellerOrdersPage />
              </ProtectedRoute>
            }
          />

          {/* ── Public Drop Routes (No Auth) ──────────────────── */}
          <Route path="/drop/:slug" element={<PublicDropPage />} />
          <Route path="/drop" element={<PublicDropPage />} />

          {/* ── Analyst Tool ──────────────────────────────────── */}
          <Route path="/analyst" element={<AutoAnalystPage />} />
          <Route path="/hackathon" element={<AutoAnalystPage />} />

          {/* ── Bionis Dashboard ──────────────────────────────── */}
          <Route path="/bionis/*" element={<BionisDashboardPage />} />
          <Route path="/bionis" element={<BionisDashboardPage />} />

          {/* ── Admin / Analytics Protected Layout ───────────── */}
          <Route
            element={
              <ProtectedRoute>
                <ProtectedLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/admin" element={<DashboardPage />} />
            <Route path="/briefing" element={<BriefingPage />} />
            <Route path="/copilot" element={<CopilotPage />} />
            <Route path="/simulator" element={<SimulatorPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/economics" element={<EconomicsPage />} />
            <Route path="/trends" element={<TrendsPage />} />
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/dataset/:id" element={<DatasetPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
