import { Routes, Route, Navigate } from 'react-router-dom'

import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './routes/Login'
import Dashboard from './routes/Dashboard'
import NotFound from './routes/NotFound'
import HardwareProductList from './routes/hardware-products/HardwareProductList'
import HardwareProductDetail from './routes/hardware-products/HardwareProductDetail'
import CompanyList from './routes/companies/CompanyList'
import CompanyDetail from './routes/companies/CompanyDetail'
import DatacenterList from './routes/datacenters/DatacenterList'
import DatacenterDetail from './routes/datacenters/DatacenterDetail'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/hardware-products" element={<HardwareProductList />} />
          <Route path="/hardware-products/:id" element={<HardwareProductDetail />} />
          <Route path="/companies" element={<CompanyList />} />
          <Route path="/companies/:id" element={<CompanyDetail />} />
          <Route path="/datacenters" element={<DatacenterList />} />
          <Route path="/datacenters/:id" element={<DatacenterDetail />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
