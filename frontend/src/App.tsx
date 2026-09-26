import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { BackendStatusProvider } from '@/hooks/useBackendStatus'
import { AuthProvider } from '@/hooks/useAuth'
import { RequireAuth } from '@/components/auth/RequireAuth'
import Dashboard from '@/pages/Dashboard'
import Repositories from '@/pages/Repositories'
import Workflow from '@/pages/Workflow'
import Findings from '@/pages/Findings'
import FindingDetailPage from '@/pages/FindingDetailPage'
import Settings from '@/pages/Settings'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import { LoadingState } from '@/components/ui/states'

const Reports = lazy(() => import('@/pages/Reports'))

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <BackendStatusProvider>
          <Routes>
            {/* Public auth routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected app routes */}
            <Route
              element={
                <RequireAuth>
                  <AppLayout />
                </RequireAuth>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="repositories" element={<Repositories />} />
              <Route path="workflow" element={<Workflow />} />
              <Route path="findings" element={<Findings />} />
              <Route path="findings/:id" element={<FindingDetailPage />} />
              <Route
                path="reports"
                element={
                  <Suspense fallback={<LoadingState message="Loading reports..." />}>
                    <Reports />
                  </Suspense>
                }
              />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </BackendStatusProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
