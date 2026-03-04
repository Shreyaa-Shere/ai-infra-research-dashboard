import { Routes, Route } from 'react-router-dom'

import Layout from './components/Layout'
import Login from './routes/Login'
import Dashboard from './routes/Dashboard'
import NotFound from './routes/NotFound'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
