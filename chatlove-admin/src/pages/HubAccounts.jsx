import { useState, useEffect } from 'react'
import { adminAPI } from '../api'
import { Plus, Server, TrendingUp, Activity, Edit, Trash2, Check, X } from 'lucide-react'
import './HubAccounts.css'

function HubAccounts() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    session_token: '',
    credits_remaining: 0,
    priority: 0
  })

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      const response = await adminAPI.getHubAccounts()
      setAccounts(response.data)
    } catch (error) {
      console.error('Error loading hub accounts:', error)
      alert('Erro ao carregar contas hub: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    
    try {
      if (editingAccount) {
        await adminAPI.updateHubAccount(editingAccount.id, formData)
      } else {
        await adminAPI.createHubAccount(formData)
      }
      
      setShowModal(false)
      setEditingAccount(null)
      setFormData({ name: '', email: '', session_token: '', credits_remaining: 0, priority: 0 })
      loadAccounts()
    } catch (error) {
      alert('Erro ao salvar: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleEdit = (account) => {
    setEditingAccount(account)
    setFormData({
      name: account.name,
      email: account.email,
      session_token: account.session_token_preview ? '' : account.session_token,
      credits_remaining: account.credits_remaining,
      priority: account.priority
    })
    setShowModal(true)
  }

  const handleDelete = async (accountId, accountName) => {
    if (!confirm(`Deletar conta "${accountName}"? Todos os mapeamentos serão perdidos.`)) {
      return
    }
    
    try {
      await adminAPI.deleteHubAccount(accountId)
      loadAccounts()
    } catch (error) {
      alert('Erro ao deletar: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleToggleActive = async (account) => {
    try {
      await adminAPI.updateHubAccount(account.id, { is_active: !account.is_active })
      loadAccounts()
    } catch (error) {
      alert('Erro ao atualizar: ' + (error.response?.data?.detail || error.message))
    }
  }

  if (loading) {
    return <div className="loading">Carregando...</div>
  }

  return (
    <div className="hub-accounts-page">
      <div className="page-header">
        <h1 className="page-title">Contas Hub</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={20} />
          <span>Nova Conta Hub</span>
        </button>
      </div>

      <div className="hub-accounts-grid">
        {accounts.map((account) => (
          <div key={account.id} className={`hub-account-card ${!account.is_active ? 'inactive' : ''}`}>
            <div className="card-header">
              <div className="account-avatar">
                <Server size={28} />
              </div>
              <div className="account-info">
                <h3>{account.name}</h3>
                <p className="account-email">{account.email}</p>
              </div>
              <div className={`status-badge ${account.is_active ? 'active' : 'inactive'}`}>
                {account.is_active ? 'Ativa' : 'Inativa'}
              </div>
            </div>

            <div className="account-stats">
              <div className="stat-row">
                <div className="stat-item">
                  <div className="stat-icon credits">
                    <TrendingUp size={20} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-label">Créditos Restantes</div>
                    <div className="stat-value">{account.credits_remaining.toFixed(2)}</div>
                  </div>
                </div>
              </div>

              <div className="stat-row">
                <div className="stat-item-small">
                  <div className="stat-label">Projetos Mapeados</div>
                  <div className="stat-value-small">{account.projects_mapped}</div>
                </div>
                <div className="stat-item-small">
                  <div className="stat-label">Total Requisições</div>
                  <div className="stat-value-small">{account.total_requests}</div>
                </div>
              </div>

              <div className="stat-row">
                <div className="stat-item-small">
                  <div className="stat-label">Tokens Usados</div>
                  <div className="stat-value-small">{account.tokens_used.toFixed(2)}</div>
                </div>
                <div className="stat-item-small">
                  <div className="stat-label">Prioridade</div>
                  <div className="stat-value-small">{account.priority}</div>
                </div>
              </div>

              {account.last_used_at && (
                <div className="last-used">
                  Último uso: {new Date(account.last_used_at).toLocaleString('pt-BR')}
                </div>
              )}
            </div>

            <div className="card-actions">
              <button 
                className={`toggle-btn ${account.is_active ? 'active' : 'inactive'}`}
                onClick={() => handleToggleActive(account)}
              >
                {account.is_active ? <X size={16} /> : <Check size={16} />}
                {account.is_active ? 'Desativar' : 'Ativar'}
              </button>
              <button className="btn-edit" onClick={() => handleEdit(account)}>
                <Edit size={16} />
                Editar
              </button>
              <button className="btn-delete" onClick={() => handleDelete(account.id, account.name)}>
                <Trash2 size={16} />
                Deletar
              </button>
            </div>
          </div>
        ))}
      </div>

      {accounts.length === 0 && (
        <div className="empty-state">
          <Server size={64} />
          <h3>Nenhuma conta hub configurada</h3>
          <p>Adicione uma conta hub para começar a economizar créditos</p>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={20} />
            Adicionar Conta Hub
          </button>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingAccount ? 'Editar Conta Hub' : 'Nova Conta Hub'}</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Nome</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Hub Account 1"
                  required
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@example.com"
                  required
                  disabled={!!editingAccount}
                />
              </div>

              <div className="form-group">
                <label>Session Token</label>
                <textarea
                  value={formData.session_token}
                  onChange={(e) => setFormData({ ...formData, session_token: e.target.value })}
                  placeholder="eyJhbGciOiJSUzI1NiIsImtpZCI6IjFjMzIxOTgzNGRhNT..."
                  rows={3}
                  required={!editingAccount}
                />
                <small>Copie de: DevTools → Application → Cookies → lovable-session-id.id</small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Créditos Iniciais</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.credits_remaining}
                    onChange={(e) => setFormData({ ...formData, credits_remaining: parseFloat(e.target.value) })}
                    placeholder="0"
                  />
                </div>

                <div className="form-group">
                  <label>Prioridade</label>
                  <input
                    type="number"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                    placeholder="0"
                  />
                  <small>Menor = maior prioridade</small>
                </div>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-primary">
                  {editingAccount ? 'Salvar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default HubAccounts