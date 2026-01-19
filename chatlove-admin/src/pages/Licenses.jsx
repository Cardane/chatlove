import { useState, useEffect } from 'react'
import { adminAPI } from '../api'
import { Plus, Copy, Check, X, Calendar, User, Trash2 } from 'lucide-react'
import './Licenses.css'

function Licenses() {
  const [licenses, setLicenses] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [copiedKey, setCopiedKey] = useState(null)
  const [selectedUserId, setSelectedUserId] = useState('')

  useEffect(() => {
    loadLicenses()
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const response = await adminAPI.getUsers()
      setUsers(response.data)
    } catch (error) {
      console.error('Error loading users:', error)
    }
  }

  const loadLicenses = async () => {
    try {
      const response = await adminAPI.getLicenses()
      setLicenses(response.data)
    } catch (error) {
      console.error('Error loading licenses:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateLicense = async () => {
    try {
      const data = selectedUserId ? { user_id: parseInt(selectedUserId) } : {}
      await adminAPI.createLicense(data)
      setShowModal(false)
      setSelectedUserId('')
      loadLicenses()
    } catch (error) {
      alert('Erro ao criar licença: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleToggleLicense = async (id, currentStatus) => {
    try {
      await adminAPI.updateLicense(id, !currentStatus)
      loadLicenses()
    } catch (error) {
      alert('Erro ao atualizar licença: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDeleteLicense = async (licenseId, licenseKey) => {
    if (!confirm(`Tem certeza que deseja deletar a licença "${licenseKey}"?`)) {
      return
    }
    try {
      await adminAPI.deleteLicense(licenseId)
      loadLicenses()
    } catch (error) {
      alert('Erro ao deletar licença: ' + (error.response?.data?.detail || error.message))
    }
  }

  const copyToClipboard = (key) => {
    navigator.clipboard.writeText(key)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  if (loading) {
    return <div className="loading">Carregando...</div>
  }

  return (
    <div className="licenses-page">
      <div className="page-header">
        <h1 className="page-title">Licenças</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={20} />
          <span>Nova Licença</span>
        </button>
      </div>

      <div className="licenses-table">
        <div className="table-header">
          <div>Chave</div>
          <div>Usuário</div>
          <div>Status</div>
          <div>Criada em</div>
          <div>Tokens</div>
          <div>Ações</div>
        </div>

        {licenses.map((license) => (
          <div key={license.id} className="table-row">
            <div className="license-key">
              <code>{license.license_key}</code>
              <button
                className="copy-btn"
                onClick={() => copyToClipboard(license.license_key)}
                title="Copiar chave"
              >
                {copiedKey === license.license_key ? (
                  <Check size={16} />
                ) : (
                  <Copy size={16} />
                )}
              </button>
            </div>

            <div className="user-cell">
              {license.user_name ? (
                <>
                  <User size={14} />
                  <span>{license.user_name}</span>
                </>
              ) : (
                <span className="no-user">Não atribuída</span>
              )}
            </div>

            <div>
              <span className={`status-badge ${license.is_used ? 'used' : 'unused'} ${license.is_active ? 'active' : 'inactive'}`}>
                {license.is_used ? 'Usada' : 'Disponível'}
                {!license.is_active && ' (Inativa)'}
              </span>
            </div>

            <div className="date-cell">
              <Calendar size={14} />
              <span>{new Date(license.created_at).toLocaleDateString('pt-BR')}</span>
            </div>

            <div className="tokens-cell">
              {license.tokens_saved.toFixed(2)}
            </div>

            <div className="actions-cell">
              <button
                className={`toggle-btn ${license.is_active ? 'active' : 'inactive'}`}
                onClick={() => handleToggleLicense(license.id, license.is_active)}
                title={license.is_active ? 'Desativar' : 'Ativar'}
              >
                {license.is_active ? 'Desativar' : 'Ativar'}
              </button>
              <button
                className="delete-btn"
                onClick={() => handleDeleteLicense(license.id, license.license_key)}
                title="Deletar licença"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nova Licença</h2>
            <div className="form-group">
              <label>Vincular a Usuário (opcional)</label>
              <select
                value={selectedUserId}
                onChange={(e) => setSelectedUserId(e.target.value)}
              >
                <option value="">Sem vínculo</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowModal(false)}>
                Cancelar
              </button>
              <button className="btn-primary" onClick={handleCreateLicense}>
                Gerar Licença
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Licenses
