import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { BackendStatusProvider } from '@/hooks/useBackendStatus'
import Dashboard from '@/pages/Dashboard'
import Repositories from '@/pages/Repositories'
import Workflow from '@/pages/Workflow'
import Findings from '@/pages/Findings'
import FindingDetailPage from '@/pages/FindingDetailPage'
import Settings from '@/pages/Settings'
import { LoadingState } from '@/components/ui/states'

const Reports = lazy(() => import('@/pages/Reports'))

export default function App() {
  return (
    <BackendStatusProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="repositories" element={<Repositories />} />
            <Route path="workflow" element={<Workflow />} />
            <Route path="findings" element={<Findings />} />
            <Route path="findings/:id" element={<FindingDetailPage />} />
            <Route path="reports" element={<Suspense fallback={<LoadingState message="Loading reports..." />}><Reports /></Suspense>} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </BackendStatusProvider>
  )
}
