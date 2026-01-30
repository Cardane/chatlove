/**
 * ChatLove Proxy - Content Script SEM INTERCEPTOR
 * Versão limpa que não interfere com fetch
 */

// Configuration
const SIDEBAR_WIDTH = '380px';
const ANIMATION_DURATION = '300ms';
const PROXY_URL = 'https://chat.trafficai.cloud/api/master-proxy';
const DEBUG = false;

// Debug logger
function log(...args) {
  if (DEBUG) console.log(...args);
}

// =============================================================================
// COOKIE CAPTURE
// =============================================================================

async function getCookieToken() {
  try {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { action: 'getCookie' },
        (response) => {
          if (response && response.cookie) {
            console.log('[ChatLove Proxy] Cookie capturado com sucesso');
            resolve(response.cookie);
          } else {
            console.error('[ChatLove Proxy] Cookie não encontrado');
            resolve(null);
          }
        }
      );
    });
  } catch (error) {
    console.error('[ChatLove Proxy] Erro ao capturar cookie:', error);
    return null;
  }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

async function init() {
  // Validate license first
  const { licenseKey } = await chrome.storage.local.get(['licenseKey']);
  
  if (!licenseKey) {
    console.log('[ChatLove Proxy] License not activated. Please activate in extension popup.');
    return;
  }
  
  // License valid, inject sidebar
  injectSidebar();
}

// =============================================================================
// INJECT SIDEBAR
// =============================================================================

function injectSidebar() {
  if (document.getElementById('chatlove-sidebar')) {
    return;
  }

  const sidebar = document.createElement('div');
  sidebar.id = 'chatlove-sidebar';
  sidebar.innerHTML = `
    <button class="cl-toggle-btn" id="cl-toggle-btn" title="Mostrar/Ocultar">
      <span class="cl-toggle-text">Chat</span>
    </button>
    
    <div class="cl-sidebar-header">
      <div class="cl-header-left">
        <span class="cl-title">ChatLove</span>
      </div>
      <button class="cl-close-btn" id="cl-close-btn" title="Minimizar">−</button>
    </div>

    <div class="cl-sidebar-content">
      <div class="cl-project-info">
        <div class="cl-project-label">Projeto Atual</div>
        <div class="cl-project-name" id="cl-project-name">Detectando...</div>
      </div>

      <div class="cl-mode-selector">
        <button class="cl-mode-btn active" data-mode="builder" title="Executa mudanças no código">
          🔨 Builder
        </button>
        <button class="cl-mode-btn" data-mode="plan" title="Apenas planejamento, sem executar">
          📋 Plan
        </button>
      </div>

      <div class="cl-stats">
        <div class="cl-stat">
          <div class="cl-stat-label">Créditos Economizados</div>
          <div class="cl-stat-value" id="cl-credits-saved">0</div>
        </div>
      </div>

      <div class="cl-save-status" id="cl-save-status">
        <span class="cl-save-icon">💾</span>
        <span class="cl-save-text">Pronto</span>
      </div>

      <div class="cl-trial-warning" id="cl-trial-warning" style="display: none;">
        <div class="cl-trial-icon">⏱️</div>
        <div class="cl-trial-text">
          <div class="cl-trial-title">Licença de Teste</div>
          <div class="cl-trial-time" id="cl-trial-time">Carregando...</div>
        </div>
      </div>

      <div class="cl-chat-container" id="cl-chat-container">
        <div class="cl-message cl-bot">
          Bem-vindo ao ChatLove! Seus créditos estão sendo economizados.
        </div>
      </div>

      <div class="cl-input-area">
        <textarea 
          id="cl-message-input" 
          placeholder="Digite sua instrução..."
          rows="3"
        ></textarea>
        <button class="cl-send-btn" id="cl-send-btn">
          <span>Enviar</span>
        </button>
      </div>

      <div class="cl-footer">
        <button class="cl-footer-btn" id="cl-clear-btn" title="Limpar histórico">
          Limpar
        </button>
        <span class="cl-status" id="cl-status">Pronto</span>
      </div>
    </div>
  `;

  document.body.appendChild(sidebar);
  injectStyles();
  initializeSidebar();
}

// =============================================================================
// INJECT STYLES
// =============================================================================

function injectStyles() {
  const style = document.createElement('style');
  style.textContent = `
    #chatlove-sidebar {
      position: fixed;
      top: 0;
      right: 0;
      width: ${SIDEBAR_WIDTH};
      height: 100vh;
      background: linear-gradient(180deg, #0f3460 0%, #16213e 100%);
      border-left: 2px solid rgba(255, 255, 255, 0.1);
      box-shadow: -5px 0 30px rgba(0, 0, 0, 0.3);
      z-index: 999999;
      display: flex;
      flex-direction: column;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #fff;
      transition: transform ${ANIMATION_DURATION} ease;
    }

    #chatlove-sidebar.minimized {
      transform: translateX(${SIDEBAR_WIDTH});
    }

    .cl-toggle-btn {
      position: fixed;
      top: 50%;
      right: 0;
      transform: translateY(-50%);
      width: 40px;
      height: 120px;
      background: linear-gradient(135deg, #E91E63, #9C27B0);
      border: none;
      border-radius: 8px 0 0 8px;
      color: white;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      z-index: 999998;
      box-shadow: -3px 0 15px rgba(233, 30, 99, 0.5);
      transition: all 0.3s ease;
      display: none;
      writing-mode: vertical-rl;
      text-orientation: mixed;
      padding: 10px 0;
    }

    #chatlove-sidebar.minimized .cl-toggle-btn {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .cl-toggle-btn:hover {
      transform: translateY(-50%) translateX(-5px);
      box-shadow: -5px 0 20px rgba(233, 30, 99, 0.7);
    }

    .cl-toggle-text {
      letter-spacing: 2px;
    }

    .cl-sidebar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background: rgba(0, 0, 0, 0.2);
      border-bottom: 2px solid rgba(233, 30, 99, 0.5);
    }

    .cl-header-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .cl-title {
      font-size: 18px;
      font-weight: 700;
      background: linear-gradient(135deg, #E91E63, #9C27B0);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .cl-close-btn {
      background: rgba(255, 255, 255, 0.1);
      border: 2px solid rgba(255, 255, 255, 0.2);
      color: #fff;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 20px;
      font-weight: bold;
      transition: all 0.2s ease;
    }

    .cl-close-btn:hover {
      background: rgba(255, 255, 255, 0.2);
      transform: scale(1.1);
    }

    .cl-sidebar-content {
      display: flex;
      flex-direction: column;
      flex: 1;
      overflow: hidden;
    }

    .cl-project-info {
      padding: 12px 16px;
      background: rgba(0, 0, 0, 0.2);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .cl-project-label {
      font-size: 11px;
      opacity: 0.7;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }

    .cl-project-name {
      font-size: 13px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .cl-mode-selector {
      padding: 12px 16px;
      background: rgba(0, 0, 0, 0.15);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      gap: 8px;
    }

    .cl-mode-btn {
      flex: 1;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.1);
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }

    .cl-mode-btn:hover {
      background: rgba(255, 255, 255, 0.2);
      transform: translateY(-1px);
    }

    .cl-mode-btn.active {
      background: linear-gradient(135deg, #E91E63, #9C27B0);
      border-color: #E91E63;
      box-shadow: 0 4px 15px rgba(233, 30, 99, 0.4);
    }

    .cl-stats {
      padding: 12px 16px;
      background: rgba(0, 0, 0, 0.15);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .cl-stat {
      text-align: center;
    }

    .cl-stat-label {
      font-size: 11px;
      opacity: 0.7;
      margin-bottom: 4px;
    }

    .cl-stat-value {
      font-size: 24px;
      font-weight: 700;
      background: linear-gradient(135deg, #4CAF50, #8BC34A);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .cl-save-status {
      padding: 8px 16px;
      background: rgba(0, 0, 0, 0.15);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
    }

    .cl-save-icon {
      font-size: 16px;
    }

    .cl-save-text {
      opacity: 0.8;
    }

    .cl-save-status.pending {
      background: rgba(255, 152, 0, 0.15);
      border-left: 3px solid #FF9800;
    }

    .cl-save-status.saved {
      background: rgba(76, 175, 80, 0.15);
      border-left: 3px solid #4CAF50;
    }

    .cl-save-status.error {
      background: rgba(244, 67, 54, 0.15);
      border-left: 3px solid #F44336;
    }

    .cl-trial-warning {
      padding: 12px 16px;
      background: rgba(255, 152, 0, 0.15);
      border-bottom: 1px solid rgba(255, 152, 0, 0.3);
      border-left: 3px solid #FF9800;
      display: flex;
      align-items: center;
      gap: 12px;
      animation: pulse-warning 2s ease-in-out infinite;
    }

    @keyframes pulse-warning {
      0%, 100% {
        background: rgba(255, 152, 0, 0.15);
      }
      50% {
        background: rgba(255, 152, 0, 0.25);
      }
    }

    .cl-trial-icon {
      font-size: 24px;
      animation: rotate 3s linear infinite;
    }

    @keyframes rotate {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    .cl-trial-text {
      flex: 1;
    }

    .cl-trial-title {
      font-size: 12px;
      font-weight: 700;
      color: #FF9800;
      margin-bottom: 4px;
    }

    .cl-trial-time {
      font-size: 14px;
      font-weight: 600;
      color: #fff;
    }

    .cl-chat-container {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .cl-chat-container::-webkit-scrollbar {
      width: 8px;
    }

    .cl-chat-container::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.2);
      border-radius: 10px;
    }

    .cl-chat-container::-webkit-scrollbar-thumb {
      background: rgba(233, 30, 99, 0.5);
      border-radius: 10px;
    }

    .cl-message {
      padding: 12px 14px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.5;
      max-width: 90%;
      word-wrap: break-word;
      animation: slideIn 0.3s ease;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .cl-message.cl-bot {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      align-self: flex-start;
    }

    .cl-message.cl-user {
      background: linear-gradient(135deg, #E91E63, #9C27B0);
      color: white;
      align-self: flex-end;
      box-shadow: 0 4px 15px rgba(233, 30, 99, 0.4);
    }

    .cl-message.cl-error {
      background: rgba(244, 67, 54, 0.2);
      border: 1px solid rgba(244, 67, 54, 0.5);
    }

    .cl-message.cl-success {
      background: rgba(76, 175, 80, 0.2);
      border: 1px solid rgba(76, 175, 80, 0.5);
    }

    .cl-message.cl-info {
      background: rgba(33, 150, 243, 0.2);
      border: 1px solid rgba(33, 150, 243, 0.5);
    }

    .cl-input-area {
      padding: 16px;
      background: rgba(0, 0, 0, 0.2);
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    #cl-message-input {
      width: 100%;
      min-height: 60px;
      max-height: 120px;
      padding: 12px;
      background: rgba(255, 255, 255, 0.1);
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 10px;
      color: #fff;
      font-size: 14px;
      font-family: inherit;
      resize: vertical;
      transition: all 0.2s ease;
    }

    #cl-message-input:focus {
      outline: none;
      border-color: #E91E63;
      box-shadow: 0 0 20px rgba(233, 30, 99, 0.3);
      background: rgba(255, 255, 255, 0.15);
    }

    #cl-message-input::placeholder {
      color: rgba(255, 255, 255, 0.5);
    }

    .cl-send-btn {
      width: 100%;
      padding: 12px;
      background: #E91E63;
      border: none;
      border-radius: 10px;
      color: white;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 4px 15px rgba(233, 30, 99, 0.4);
    }

    .cl-send-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(233, 30, 99, 0.6);
      background: #C2185B;
    }

    .cl-send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    .cl-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: rgba(0, 0, 0, 0.2);
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .cl-footer-btn {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #fff;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .cl-footer-btn:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    .cl-status {
      font-size: 12px;
      opacity: 0.7;
    }

    body.cl-sidebar-active {
      margin-right: ${SIDEBAR_WIDTH};
    }
  `;

  document.head.appendChild(style);
}

// =============================================================================
// INITIALIZE SIDEBAR
// =============================================================================

function initializeSidebar() {
  const sidebar = document.getElementById('chatlove-sidebar');
  const closeBtn = document.getElementById('cl-close-btn');
  const sendBtn = document.getElementById('cl-send-btn');
  const clearBtn = document.getElementById('cl-clear-btn');
  const messageInput = document.getElementById('cl-message-input');
  const chatContainer = document.getElementById('cl-chat-container');
  const projectName = document.getElementById('cl-project-name');
  const status = document.getElementById('cl-status');
  const creditsSaved = document.getElementById('cl-credits-saved');

  document.body.classList.add('cl-sidebar-active');

  // Detect project
  detectProject();

  // Load stats and check license status
  loadStats();
  checkLicenseStatus();
  
  // Check license status every 10 seconds
  setInterval(checkLicenseStatus, 10000);

  // Toggle button
  const toggleBtn = document.getElementById('cl-toggle-btn');
  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('minimized');
    document.body.classList.toggle('cl-sidebar-active');
  });

  // Close button
  closeBtn.addEventListener('click', () => {
    sidebar.classList.toggle('minimized');
    document.body.classList.toggle('cl-sidebar-active');
  });

  // Mode selector buttons
  const modeButtons = document.querySelectorAll('.cl-mode-btn');
  modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Remove active from all buttons
      modeButtons.forEach(b => b.classList.remove('active'));
      // Add active to clicked button
      btn.classList.add('active');
      
      const mode = btn.dataset.mode;
      console.log('[ChatLove] Modo alterado para:', mode);
      
      // Update placeholder based on mode
      if (mode === 'plan') {
        messageInput.placeholder = 'Digite sua pergunta (apenas planejamento)...';
        addMessage('🔄 Modo Plan ativado: IA apenas responderá, sem executar código.', 'info');
      } else {
        messageInput.placeholder = 'Digite sua instrução (execução de código)...';
        addMessage('🔄 Modo Builder ativado: IA executará mudanças no código.', 'info');
      }
    });
  });

  // Send button
  sendBtn.addEventListener('click', () => sendMessage());

  // Enter to send
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Clear button
  clearBtn.addEventListener('click', () => {
    chatContainer.innerHTML = '<div class="cl-message cl-bot">Histórico limpo!</div>';
    setStatus('Limpo');
  });

  async function detectProject() {
    const match = window.location.pathname.match(/\/projects\/([a-f0-9-]+)/i);
    
    if (match) {
      const projectId = match[1];
      
      // Fallback: mostrar ID abreviado
      projectName.textContent = projectId.substring(0, 8) + '...';
      projectName.title = projectId;
      console.log('[ChatLove Proxy] Projeto detectado:', projectId);
      return projectId;
    } else {
      projectName.textContent = 'Projeto não detectado';
      return null;
    }
  }

  function addMessage(text, type = 'bot') {
    const message = document.createElement('div');
    message.className = `cl-message cl-${type}`;
    message.textContent = text;
    chatContainer.appendChild(message);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  function setStatus(text) {
    status.textContent = text;
  }

  async function loadStats() {
    // Desabilitado para evitar CORS
    creditsSaved.textContent = '0';
  }

  function updateSaveStatus(status, text) {
    const saveStatus = document.getElementById('cl-save-status');
    const saveText = saveStatus.querySelector('.cl-save-text');
    const saveIcon = saveStatus.querySelector('.cl-save-icon');
    
    // Remove all status classes
    saveStatus.classList.remove('pending', 'saved', 'error');
    
    // Add new status
    if (status !== 'ready') {
      saveStatus.classList.add(status);
    }
    
    // Update text and icon
    saveText.textContent = text;
    
    switch (status) {
      case 'pending':
        saveIcon.textContent = '⏳';
        break;
      case 'saved':
        saveIcon.textContent = '✅';
        break;
      case 'error':
        saveIcon.textContent = '❌';
        break;
      default:
        saveIcon.textContent = '💾';
    }
  }

  async function checkLicenseStatus() {
    // Desabilitado para evitar CORS
    const sendBtn = document.getElementById('cl-send-btn');
    sendBtn.disabled = false;
    sendBtn.textContent = 'Enviar';
  }

  async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) {
      setStatus('Digite uma mensagem');
      return;
    }

    const projectId = await detectProject();
    if (!projectId) {
      addMessage('Erro: Projeto não detectado', 'error');
      setStatus('Erro');
      return;
    }

    // Get selected mode
    const activeMode = document.querySelector('.cl-mode-btn.active');
    const mode = activeMode ? activeMode.dataset.mode : 'builder';
    
    console.log('[ChatLove] Enviando mensagem em modo:', mode);

    // Get license key
    const { licenseKey } = await chrome.storage.local.get(['licenseKey']);
    if (!licenseKey) {
      addMessage('Erro: Licença não ativada', 'error');
      setStatus('Erro');
      return;
    }

    // Capturar cookie automaticamente
    setStatus('Capturando cookie...');
    const sessionToken = await getCookieToken();
    
    if (!sessionToken) {
      addMessage('Erro: Não foi possível capturar o cookie. Faça login no Lovable.', 'error');
      setStatus('Erro');
      return;
    }

    updateSaveStatus('pending', 'Enviando...');

    addMessage(message, 'user');
    messageInput.value = '';
    
    sendBtn.disabled = true;
    setStatus('Enviando ao proxy...');

    try {
      console.log('[ChatLove Proxy] Enviando para:', PROXY_URL);
      console.log('[ChatLove Proxy] Dados:', { 
        license_key: licenseKey, 
        project_id: projectId, 
        message: message.substring(0, 50),
        mode: mode
      });
      
      // Usar fetch nativo sem interceptação
      const response = await window.fetch(PROXY_URL, {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          license_key: licenseKey,
          project_id: projectId,
          message: message,
          session_token: sessionToken,
          mode: mode
        })
      });

      console.log('[ChatLove Proxy] Response status:', response.status);
      console.log('[ChatLove Proxy] Response ok:', response.ok);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[ChatLove Proxy] Erro HTTP:', errorData);
        const errorMessage = errorData.detail || errorData.message || 'Erro ao enviar mensagem';
        addMessage(`Erro: ${errorMessage}`, 'error');
        setStatus('Erro');
        updateSaveStatus('error', 'Erro no envio');
        return;
      }

      const data = await response.json();
      console.log('[ChatLove Proxy] Response data:', data);

      if (data.success) {
        const modeText = mode === 'plan' ? '(Modo Plan)' : '(Modo Builder)';
        addMessage(`✅ Mensagem enviada com sucesso! ${modeText}`, 'success');
        console.log('[ChatLove Proxy] Sucesso! Mensagem enviada.');
        
        setStatus('✅ Enviado');
        updateSaveStatus('saved', 'Enviado com sucesso');
      } else {
        const errorMessage = data.message || data.detail || 'Erro desconhecido';
        console.error('[ChatLove Proxy] Erro do servidor:', errorMessage);
        addMessage(`Erro: ${errorMessage}`, 'error');
        setStatus('Erro');
        updateSaveStatus('error', 'Erro do servidor');
      }

    } catch (error) {
      console.error('[ChatLove Proxy] Erro catch:', error);
      
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        addMessage('❌ Erro CORS: Precisa corrigir servidor', 'error');
        setStatus('Erro CORS');
        updateSaveStatus('error', 'Erro CORS');
      } else {
        addMessage(`Erro: ${error.message}`, 'error');
        setStatus('Erro');
        updateSaveStatus('error', 'Erro na requisição');
      }
    } finally {
      sendBtn.disabled = false;
    }
  }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

console.log('♥ ChatLove Proxy loaded! (SEM INTERCEPTOR)');