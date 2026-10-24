import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Store,
  Tag,
  Package,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  ChevronRight,
  TrendingUp,
} from 'lucide-react'

export default function SellerLayout({ children, storeSlug, storeName, upiId }) {
  const location = useLocation()

  const navItems = [
    {
      name: 'Business Setup',
      path: '/seller/setup',
      icon: Store,
      badge: 'Step 1',
      active: location.pathname === '/seller/setup',
    },
    {
      name: 'Item Lister',
      path: '/seller/lister',
      icon: Tag,
      badge: 'Step 2',
      active: location.pathname === '/seller/lister',
    },
    {
      name: 'Orders & Shipping',
      path: '/seller/orders',
      icon: Package,
      badge: 'Step 3',
      active: location.pathname === '/seller/orders',
    },
  ]

  const publicUrl = storeSlug ? `/drop/${storeSlug}` : '/drop'

  return (
    <div className="bionis-root flex min-h-screen bg-[#070a12] text-slate-100 selection:bg-blue-600 selection:text-white">
      {/* ── Bionis Desktop Sidebar ──────────────────────────────── */}
      <aside className="hidden lg:flex w-72 flex-col justify-between border-r border-slate-800/80 bg-[#090d16]/95 backdrop-blur-xl p-5 shrink-0 sticky top-0 h-screen">
        <div>
          {/* Brand Header */}
          <div className="flex items-center gap-3 px-2 py-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white font-black text-xl tracking-wider">
              T
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">TrendPulse</span>
                <span className="text-[10px] uppercase font-bold tracking-widest bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1.5 py-0.5 rounded">
                  Seller
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium">IG Thrift Operating System</p>
            </div>
          </div>

          {/* Back to Dashboard */}
          <Link
            to="/dashboard"
            className="flex items-center gap-2 px-3 py-2 mb-4 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all"
          >
            <span>←</span>
            <span>Back to Dashboard</span>
          </Link>

          {/* Navigation Section */}
          <div className="space-y-1">
            <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Onboarding & Workflow
            </p>
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    item.active
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm shadow-blue-500/10'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${item.active ? 'text-blue-400' : 'text-slate-400'}`} />
                    <span>{item.name}</span>
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                      item.active
                        ? 'bg-blue-500/20 text-blue-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                </Link>
              )
            })}
          </div>

          {/* Quick Zero-Custody Callout */}
          <div className="mt-8 mx-1 p-3.5 rounded-xl bg-gradient-to-b from-slate-900/90 to-slate-900/40 border border-emerald-500/20 shadow-inner">
            <div className="flex items-center gap-2 text-emerald-400 mb-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span className="text-xs font-semibold">Zero-Custody Protocol</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Payments route 100% directly to your personal UPI ID. ₹0 platform cuts, ₹0 delays.
            </p>
            {upiId && (
              <div className="mt-2.5 flex items-center justify-between text-[11px] bg-emerald-950/40 border border-emerald-500/20 px-2 py-1 rounded-md text-emerald-300 font-mono">
                <span className="truncate max-w-[150px]">{upiId}</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              </div>
            )}
          </div>
        </div>

        {/* Bottom Storefront Link */}
        <div className="pt-4 border-t border-slate-800/80">
          <a
            href={publicUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 hover:bg-slate-850 border border-slate-800 transition-all group"
          >
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                <Store className="w-4 h-4" />
              </div>
              <div className="overflow-hidden text-left">
                <p className="text-xs font-semibold text-white truncate">
                  {storeName || 'My Storefront'}
                </p>
                <p className="text-[10px] text-slate-400 font-mono truncate">
                  {storeSlug ? `/drop/${storeSlug}` : 'Not configured'}
                </p>
              </div>
            </div>
            <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 transition-colors shrink-0" />
          </a>
        </div>
      </aside>

      {/* ── Main Work Area ──────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar Navigation */}
        <header className="h-16 border-b border-slate-800/80 bg-[#090d16]/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-2.5 text-sm">
            <span className="text-slate-400 font-medium">Seller Studio</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
            <span className="text-white font-semibold">Business Onboarding & Profile</span>
          </div>

          <div className="flex items-center gap-4">
            {/* Live Status Pill */}
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 bionis-live-pulse" />
              <span>Step 1: Setup Active</span>
            </div>

            {/* Public Link Button */}
            <a
              href={publicUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-xs font-medium text-slate-200 hover:text-white transition-all shadow-sm"
            >
              <span>View Live Drop</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </header>

        {/* Dynamic Screen Outlet */}
        <main className="flex-1 p-6 md:p-10 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  )
}
