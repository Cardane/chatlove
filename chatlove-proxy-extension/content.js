/**
 * ChatLove Proxy - Content Script
 * Versão que economiza 95% dos créditos do Lovable
 * 
 * Estratégia:
 * 1. Envia mensagens para proxy local (não consome créditos)
 * 2. Injeta no campo do Lovable (preview atualiza)
 * 3. NÃO clica em enviar (não salva)
 * 4. Usuário clica manualmente quando quiser salvar (1 crédito)
 */

// Configuration
const SIDEBAR_WIDTH = '380px';
const ANIMATION_DURATION = '300ms';
const PROXY_URL = 'https://209.38.79.211/api/master-proxy';
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
    // Content scripts não têm acesso direto a chrome.cookies
    // Precisamos usar messaging para pedir ao background script
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

      <div class="cl-stats">
        <div class="cl-stat">
          <div class="cl-stat-label">Créditos Economizados</div>
          <div class="cl-stat-value" id="cl-credits-saved">0</div>
        </div>
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

    .cl-logo {
      font-size: 24px;
      animation: pulse 2s ease-in-out infinite;
      filter: drop-shadow(0 0 10px rgba(233, 30, 99, 0.5));
    }

    @keyframes pulse {
      0%, 100% { 
        transform: scale(1);
        filter: drop-shadow(0 0 10px rgba(233, 30, 99, 0.5));
      }
      50% { 
        transform: scale(1.1);
        filter: drop-shadow(0 0 20px rgba(233, 30, 99, 0.8));
      }
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

    .cl-info-box {
      padding: 12px 16px;
      background: rgba(76, 175, 80, 0.1);
      border-bottom: 1px solid rgba(76, 175, 80, 0.3);
      border-left: 3px solid #4CAF50;
    }

    .cl-info-title {
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 6px;
      color: #4CAF50;
    }

    .cl-info-text {
      font-size: 11px;
      line-height: 1.5;
      opacity: 0.9;
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
      
      // Tentar buscar nome do projeto via API
      try {
        const sessionToken = await getCookieToken();
        
        if (sessionToken) {
          const response = await fetch(
            `https://api.lovable.dev/projects/${projectId}`,
            {
              headers: {
                "Authorization": `Bearer ${sessionToken}`,
                "Content-Type": "application/json"
              }
            }
          );
          
          if (response.ok) {
            const data = await response.json();
            const name = data.name || data.title || projectId;
            projectName.textContent = name;
            projectName.title = `${name} (${projectId})`;
            console.log('[ChatLove Proxy] Projeto detectado:', name);
            return projectId;
          }
        }
      } catch (error) {
        console.error('[ChatLove Proxy] Erro ao buscar nome do projeto:', error);
      }
      
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
    const { licenseKey } = await chrome.storage.local.get(['licenseKey']);
    
    if (!licenseKey) {
      creditsSaved.textContent = '0';
      return;
    }
    
    try {
      const response = await fetch(
        `https://209.38.79.211/api/credits/total/${licenseKey}`
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          creditsSaved.textContent = Math.floor(data.total_credits);
        }
      }
    } catch (error) {
      console.error('[ChatLove] Erro ao carregar créditos:', error);
      creditsSaved.textContent = '0';
    }
  }

  function injectMessageToLovable(message) {
    try {
      console.log('[ChatLove Proxy] Injetando mensagem no Lovable...');
      
      // Encontrar campo TipTap
      const chatInput = document.querySelector('div.tiptap[contenteditable="true"]') ||
                        document.querySelector('[contenteditable="true"]');
      
      if (!chatInput) {
        console.error('[ChatLove Proxy] Campo não encontrado');
        return false;
      }

      // Injetar mensagem
      chatInput.textContent = message;
      chatInput.focus();
      
      // Disparar eventos
      chatInput.dispatchEvent(new Event('input', { bubbles: true }));
      chatInput.dispatchEvent(new Event('change', { bubbles: true }));
      
      // Aguardar um momento para o TipTap processar
      setTimeout(() => {
        // Encontrar botão de envio (último botão submit)
        const allButtons = Array.from(document.querySelectorAll('button[type="submit"]'));
        const sendButton = allButtons[allButtons.length - 1];
        
        if (sendButton) {
          console.log('[ChatLove Proxy] Clicando no botão de envio...');
          sendButton.click();
          console.log('[ChatLove Proxy] Mensagem enviada! Preview vai atualizar.');
        } else {
          console.error('[ChatLove Proxy] Botão de envio não encontrado');
        }
      }, 300);
      
      return true;
    } catch (error) {
      console.error('[ChatLove Proxy] Erro ao injetar:', error);
      return false;
    }
  }

  async function checkLicenseStatus() {
    const { licenseKey } = await chrome.storage.local.get(['licenseKey']);
    
    if (!licenseKey) return;
    
    try {
      const response = await fetch('https://209.38.79.211/api/validate-license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: licenseKey })
      });
      
      const data = await response.json();
      
      const trialWarning = document.getElementById('cl-trial-warning');
      const trialTime = document.getElementById('cl-trial-time');
      const sendBtn = document.getElementById('cl-send-btn');
      
      if (!data.success || !data.valid) {
        // Licença inválida/desativada/expirada
        trialWarning.style.display = 'flex';
        trialTime.textContent = data.message || 'Licença bloqueada';
        sendBtn.disabled = true;
        sendBtn.textContent = 'Bloqueado';
        return;
      }
      
      // Licença válida - verificar se é trial
      if (data.license_type === 'trial' && data.expires_at) {
        const now = new Date();
        const expires = new Date(data.expires_at);
        const diff = expires - now;
        
        if (diff > 0) {
          // Trial ativa - mostrar contador
          const minutes = Math.floor(diff / 60000);
          const seconds = Math.floor((diff % 60000) / 1000);
          
          trialWarning.style.display = 'flex';
          trialTime.textContent = `${minutes}m ${seconds}s restantes`;
          sendBtn.disabled = false;
          sendBtn.textContent = 'Enviar';
        } else {
          // Trial expirada
          trialWarning.style.display = 'flex';
          trialTime.textContent = 'Licença expirada';
          sendBtn.disabled = true;
          sendBtn.textContent = 'Bloqueado';
        }
      } else {
        // Licença full - esconder aviso
        trialWarning.style.display = 'none';
        sendBtn.disabled = false;
        sendBtn.textContent = 'Enviar';
      }
    } catch (error) {
      console.error('[ChatLove] Erro ao verificar licença:', error);
    }
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

    // Get license key
    const { licenseKey } = await chrome.storage.local.get(['licenseKey']);
    if (!licenseKey) {
      addMessage('Erro: Licença não ativada', 'error');
      setStatus('Erro');
      return;
    }

    // Verificar status da licença antes de enviar
    try {
      const validateResponse = await fetch('http://209.38.79.211/api/validate-license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: licenseKey })
      });
      
      const validateData = await validateResponse.json();
      
      if (!validateData.success || !validateData.valid) {
        addMessage(`Erro: ${validateData.message}`, 'error');
        setStatus('Bloqueado');
        sendBtn.disabled = true;
        return;
      }
    } catch (error) {
      console.error('[ChatLove] Erro ao validar licença:', error);
    }

    // Capturar cookie automaticamente
    setStatus('Capturando cookie...');
    const sessionToken = await getCookieToken();
    
    if (!sessionToken) {
      addMessage('Erro: Não foi possível capturar o cookie. Faça login no Lovable.', 'error');
      setStatus('Erro');
      return;
    }

    addMessage(message, 'user');
    messageInput.value = '';
    
    sendBtn.disabled = true;
    setStatus('Enviando ao proxy...');

    try {
      // Enviar para proxy com session_token
      const response = await fetch(PROXY_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          license_key: licenseKey,
          project_id: projectId,
          message: message,
          session_token: sessionToken  // ← Cookie capturado automaticamente
        })
      });

      if (!response.ok) {
        // Erro HTTP (403, 404, etc)
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || errorData.message || 'Erro ao enviar mensagem';
        addMessage(`Erro: ${errorMessage}`, 'error');
        setStatus('Erro');
        return;
      }

      const data = await response.json();

      if (data.success) {
        // Mensagem enviada com sucesso para o servidor
        // O servidor já enviou para a API do Lovable
        // NÃO precisamos injetar no DOM (evita duplicação)
        
        addMessage('Mensagem enviada com sucesso!', 'success');
        
        // Recarregar estatísticas do servidor
        await loadStats();
        
        setStatus('Enviado');
      } else {
        const errorMessage = data.message || data.detail || 'Erro desconhecido';
        addMessage(`Erro: ${errorMessage}`, 'error');
        setStatus('Erro');
      }

    } catch (error) {
      console.error('[ChatLove Proxy] Erro:', error);
      addMessage(`Erro: ${error.message}`, 'error');
      setStatus('Erro');
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

console.log('♥ ChatLove Proxy loaded!');
