import { useState, useEffect } from 'react'
import { adminAPI } from '../api'
import { Users, Key, TrendingUp, Activity } from 'lucide-react'
import './Dashboard.css'

function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const adminRole = localStorage.getItem('admin_role')

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await adminAPI.getDashboard()
      setStats(response.data)
    } catch (error) {
      console.error('Error loading stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Carregando...</div>
  }

  return (
    <div className="dashboard">
      <h1 className="page-title">Dashboard</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon users">
            <Users size={24} />
          </div>
          <div className="stat-content">
            <div className="stat-label">Total de Usuários</div>
            <div className="stat-value">{stats?.total_users || 0}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon licenses">
            <Key size={24} />
          </div>
          <div className="stat-content">
            <div className="stat-label">Licenças Ativas</div>
            <div className="stat-value">{stats?.active_licenses || 0}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon tokens">
            <TrendingUp size={24} />
          </div>
          <div className="stat-content">
            <div className="stat-label">Tokens Economizados</div>
            <div className="stat-value">{stats?.total_tokens_saved?.toFixed(2) || '0.00'}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon requests">
            <Activity size={24} />
          </div>
          <div className="stat-content">
            <div className="stat-label">Total de Requisições</div>
            <div className="stat-value">{stats?.total_requests || 0}</div>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h2>Bem-vindo ao ChatLove Admin</h2>
        <p>Gerencie usuários, licenças e acompanhe o uso do sistema.</p>
        
        {adminRole === 'master' && (
          <div className="quick-actions">
            <a href="/users" className="action-btn">
              <Users size={20} />
              <span>Gerenciar Usuários</span>
            </a>
            <a href="/licenses" className="action-btn">
              <Key size={20} />
              <span>Gerenciar Licenças</span>
            </a>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
