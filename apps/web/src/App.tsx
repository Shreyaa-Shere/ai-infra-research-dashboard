import { Routes, Route, Navigate } from 'react-router-dom'

import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'
import Login from './routes/Login'
import Dashboard from './routes/Dashboard'
import NotFound from './routes/NotFound'
import HardwareProductList from './routes/hardware-products/HardwareProductList'
import HardwareProductDetail from './routes/hardware-products/HardwareProductDetail'
import CompanyList from './routes/companies/CompanyList'
import CompanyDetail from './routes/companies/CompanyDetail'
import DatacenterList from './routes/datacenters/DatacenterList'
import DatacenterDetail from './routes/datacenters/DatacenterDetail'
import NoteList from './routes/notes/NoteList'
import NoteEditor from './routes/notes/NoteEditor'
import PublishedNote from './routes/published/PublishedNote'
import SourceList from './routes/sources/SourceList'
import SourceDetail from './routes/sources/SourceDetail'
import SearchPage from './routes/search/SearchPage'
import AcceptInvitePage from './routes/accept-invite/AcceptInvitePage'
import ForgotPasswordPage from './routes/forgot-password/ForgotPasswordPage'
import ResetPasswordPage from './routes/reset-password/ResetPasswordPage'
import UsersPage from './routes/admin/UsersPage'
import AuditLogPage from './routes/admin/AuditLogPage'
import SystemInfoPage from './routes/admin/SystemInfoPage'
import MetricSeriesList from './routes/metric-series/MetricSeriesList'
import MetricSeriesDetail from './routes/metric-series/MetricSeriesDetail'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      {/* Public routes — no auth required */}
      <Route path="/published/:slug" element={<PublishedNote />} />
      <Route path="/accept-invite" element={<AcceptInvitePage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/hardware-products" element={<HardwareProductList />} />
          <Route path="/hardware-products/:id" element={<HardwareProductDetail />} />
          <Route path="/companies" element={<CompanyList />} />
          <Route path="/companies/:id" element={<CompanyDetail />} />
          <Route path="/datacenters" element={<DatacenterList />} />
          <Route path="/datacenters/:id" element={<DatacenterDetail />} />
          <Route path="/notes" element={<NoteList />} />
          <Route path="/notes/new" element={<NoteEditor />} />
          <Route path="/notes/:id" element={<NoteEditor />} />
          <Route path="/sources" element={<SourceList />} />
          <Route path="/sources/:id" element={<SourceDetail />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/metric-series" element={<MetricSeriesList />} />
          <Route path="/metric-series/:id" element={<MetricSeriesDetail />} />
          {/* Admin-only routes */}
          <Route element={<AdminRoute />}>
            <Route path="/admin/users" element={<UsersPage />} />
            <Route path="/admin/audit-log" element={<AuditLogPage />} />
            <Route path="/admin/system" element={<SystemInfoPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
