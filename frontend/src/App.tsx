import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { BackendStatusProvider } from '@/hooks/useBackendStatus'
import Dashboard from '@/pages/Dashboard'
import Repositories from '@/pages/Repositories'
import Workflow from '@/pages/Workflow'
import Findings from '@/pages/Findings'
import FindingDetailPage from '@/pages/FindingDetailPage'
import Reports from '@/pages/Reports'
import Settings from '@/pages/Settings'

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
            <Route path="reports" element={<Reports />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </BackendStatusProvider>
  )
}
