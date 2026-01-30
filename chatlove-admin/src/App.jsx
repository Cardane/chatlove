import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Users from './pages/Users'
import Licenses from './pages/Licenses'
import HubAccounts from './pages/HubAccounts'
import Layout from './components/Layout'

function App() {
  const [token, setToken] = useState(localStorage.getItem('admin_token'))
  const [adminRole, setAdminRole] = useState(localStorage.getItem('admin_role'))

  const handleLogin = (newToken, role) => {
    localStorage.setItem('admin_token', newToken)
    localStorage.setItem('admin_role', role)
    setToken(newToken)
    setAdminRole(role)
  }

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_role')
    setToken(null)
    setAdminRole(null)
  }

  if (!token) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <BrowserRouter>
      <Layout onLogout={handleLogout}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/users" element={<Users />} />
          <Route path="/licenses" element={<Licenses />} />
          <Route path="/hub-accounts" element={<HubAccounts />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
