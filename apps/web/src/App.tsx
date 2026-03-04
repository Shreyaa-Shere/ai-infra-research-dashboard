import { Routes, Route, Navigate } from 'react-router-dom'

import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './routes/Login'
import Dashboard from './routes/Dashboard'
import NotFound from './routes/NotFound'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
