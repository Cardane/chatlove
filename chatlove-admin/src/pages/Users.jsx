import { useState, useEffect } from 'react'
import { adminAPI } from '../api'
import { Plus, Mail, Calendar, Edit, Trash2 } from 'lucide-react'
import './Users.css'

function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [newUser, setNewUser] = useState({ name: '', email: '' })
  const adminRole = localStorage.getItem('admin_role')

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const response = await adminAPI.getUsers()
      setUsers(response.data)
    } catch (error) {
      console.error('Error loading users:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async (e) => {
    e.preventDefault()
    try {
      if (editingUser) {
        await adminAPI.updateUser(editingUser.id, newUser)
      } else {
        await adminAPI.createUser(newUser)
      }
      setShowModal(false)
      setEditingUser(null)
      setNewUser({ name: '', email: '' })
      loadUsers()
    } catch (error) {
      console.error('Error creating/updating user:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Erro desconhecido'
      alert('Erro ao salvar usuário: ' + errorMsg)
    }
  }

  const handleEditUser = (user) => {
    setEditingUser(user)
    setNewUser({ name: user.name, email: user.email || '' })
    setShowModal(true)
  }

  const handleDeleteUser = async (userId, userName) => {
    if (!confirm(`Tem certeza que deseja deletar o usuário "${userName}"?`)) {
      return
    }
    try {
      await adminAPI.deleteUser(userId)
      loadUsers()
    } catch (error) {
      alert('Erro ao deletar usuário: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingUser(null)
    setNewUser({ name: '', email: '' })
  }

  if (loading) {
    return <div className="loading">Carregando...</div>
  }

  return (
    <div className="users-page">
      <div className="page-header">
        <h1 className="page-title">Usuários</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={20} />
          <span>Novo Usuário</span>
        </button>
      </div>

      <div className="users-grid">
        {users.map((user) => (
          <div key={user.id} className="user-card">
            <div className="user-avatar">{user.name.charAt(0).toUpperCase()}</div>
            <div className="user-info">
              <h3>{user.name}</h3>
              {user.email && (
                <div className="user-detail">
                  <Mail size={14} />
                  <span>{user.email}</span>
                </div>
              )}
              <div className="user-detail">
                <Calendar size={14} />
                <span>{new Date(user.created_at).toLocaleDateString('pt-BR')}</span>
              </div>
            </div>
            <div className="user-stats">
              <div className="stat-item">
                <span className="stat-label">Licenças</span>
                <span className="stat-value">{user.licenses_count}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Tokens</span>
                <span className="stat-value">{user.tokens_saved.toFixed(2)}</span>
              </div>
            </div>
            <div className="user-card-actions">
              <button className="btn-edit" onClick={() => handleEditUser(user)}>
                <Edit size={16} />
                Editar
              </button>
              {adminRole === 'master' && (
                <button className="btn-delete" onClick={() => handleDeleteUser(user.id, user.name)}>
                  <Trash2 size={16} />
                  Deletar
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingUser ? 'Editar Usuário' : 'Novo Usuário'}</h2>
            <form onSubmit={handleCreateUser}>
              <div className="form-group">
                <label>Nome</label>
                <input
                  type="text"
                  value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  required
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label>Email (opcional)</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={handleCloseModal}>
                  Cancelar
                </button>
                <button type="submit" className="btn-primary">
                  {editingUser ? 'Salvar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Users
