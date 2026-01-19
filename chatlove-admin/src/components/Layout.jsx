import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Users, Key, LogOut } from 'lucide-react'
import './Layout.css'

function Layout({ children, onLogout }) {
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="logo">♥</span>
          <h1>ChatLove Admin</h1>
        </div>

        <nav className="sidebar-nav">
          <Link
            to="/"
            className={`nav-item ${isActive('/') ? 'active' : ''}`}
          >
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </Link>

          <Link
            to="/users"
            className={`nav-item ${isActive('/users') ? 'active' : ''}`}
          >
            <Users size={20} />
            <span>Usuários</span>
          </Link>

          <Link
            to="/licenses"
            className={`nav-item ${isActive('/licenses') ? 'active' : ''}`}
          >
            <Key size={20} />
            <span>Licenças</span>
          </Link>
        </nav>

        <button className="logout-btn" onClick={onLogout}>
          <LogOut size={20} />
          <span>Sair</span>
        </button>
      </aside>

      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

export default Layout
