/**
 * ChatLove - Content Script
 * Injects sidebar into Lovable.dev with license validation
 */

// Configuration
const SIDEBAR_WIDTH = '380px';
const ANIMATION_DURATION = '300ms';
const API_URL = 'http://127.0.0.1:8000';

// =============================================================================
// INITIALIZATION
// =============================================================================

async function init() {
  // Validate license first
  const response = await chrome.runtime.sendMessage({ action: 'validateLicense' });
  
  if (!response.success || !response.valid) {
    console.log('[ChatLove] License not activated. Please activate in extension popup.');
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
    <div class="cl-sidebar-header">
      <div class="cl-header-left">
        <span class="cl-logo">♥</span>
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
          <div class="cl-stat-label">Tokens Economizados</div>
          <div class="cl-stat-value" id="cl-tokens-saved">0.00</div>
        </div>
      </div>

      <div class="cl-chat-container" id="cl-chat-container">
        <div class="cl-message cl-bot">
          ♥ Bem-vindo ao ChatLove! Seus tokens estão sendo economizados automaticamente.
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
      transform: translateX(calc(${SIDEBAR_WIDTH} - 50px));
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
      background: linear-gradient(135deg, #E91E63, #9C27B0);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
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
      background: linear-gradient(135deg, #E91E63, #9C27B0);
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
  const tokensSaved = document.getElementById('cl-tokens-saved');

  document.body.classList.add('cl-sidebar-active');

  // Detect project
  detectProject();

  // Load stats
  loadStats();

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
    chatContainer.innerHTML = '<div class="cl-message cl-bot">♥ Histórico limpo!</div>';
    setStatus('Limpo');
  });

  function detectProject() {
    // Suporta URLs: /projects/uuid ou lovable.dev/projects/uuid
    const match = window.location.pathname.match(/\/projects\/([a-f0-9-]+)/i) ||
                  window.location.href.match(/\/projects\/([a-f0-9-]+)/i);
    
    if (match) {
      const projectId = match[1];
      projectName.textContent = projectId.substring(0, 8) + '...';
      projectName.title = projectId;
      console.log('[ChatLove] Projeto detectado:', projectId);
      return projectId;
    } else {
      projectName.textContent = 'Projeto não detectado';
      console.log('[ChatLove] URL atual:', window.location.href);
      console.log('[ChatLove] Pathname:', window.location.pathname);
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
    const stats = await chrome.storage.local.get(['chatlove_stats']);
    if (stats.chatlove_stats) {
      tokensSaved.textContent = stats.chatlove_stats.tokens_saved.toFixed(2);
    }
  }

  /**
   * Injeta mensagem diretamente no chat do Lovable via DOM
   * @param {string} message - Mensagem a ser enviada
   * @returns {boolean} - true se sucesso, false se erro
   */
  function injectMessageToLovable(message) {
    try {
      console.log('[ChatLove] Iniciando injeção de mensagem...');
      
      // 1. Encontrar o campo de chat (DIV contenteditable - TipTap editor)
      const chatInput = document.querySelector('div.tiptap[contenteditable="true"]') ||
                        document.querySelector('[contenteditable="true"]');
      
      if (!chatInput) {
        console.error('[ChatLove] Campo de chat do Lovable não encontrado');
        console.log('[ChatLove] Contenteditable disponíveis:', document.querySelectorAll('[contenteditable="true"]'));
        return false;
      }

      console.log('[ChatLove] Campo de chat do Lovable encontrado:', chatInput);
      console.log('[ChatLove] Tag:', chatInput.tagName, 'Classes:', chatInput.className);

      // 2. Injetar a mensagem (usar textContent para contenteditable)
      chatInput.textContent = message;
      chatInput.focus();
      
      // 3. Disparar eventos para o TipTap/React detectar a mudança
      const inputEvent = new Event('input', { bubbles: true });
      const changeEvent = new Event('change', { bubbles: true });
      
      chatInput.dispatchEvent(inputEvent);
      chatInput.dispatchEvent(changeEvent);
      
      // 4. Encontrar o botão de envio (último botão submit com SVG)
      const allButtons = Array.from(document.querySelectorAll('button[type="submit"]'));
      const sendButton = allButtons[allButtons.length - 1]; // Último botão submit
      
      if (!sendButton) {
        console.error('[ChatLove] Botão de envio do Lovable não encontrado');
        console.log('[ChatLove] Botões submit disponíveis:', allButtons.length);
        return false;
      }

      console.log('[ChatLove] Botão de envio do Lovable encontrado:', sendButton);
      console.log('[ChatLove] Classes:', sendButton.className);

      // 5. Aguardar um momento para o TipTap processar e clicar UMA VEZ
      setTimeout(() => {
        sendButton.click();
        console.log('[ChatLove] Mensagem injetada com sucesso!');
      }, 300);

      return true;
    } catch (error) {
      console.error('[ChatLove] Erro ao injetar mensagem:', error);
      return false;
    }
  }

  async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) {
      setStatus('Digite uma mensagem');
      return;
    }

    const projectId = detectProject();
    if (!projectId) {
      addMessage('❌ Erro: Projeto não detectado', 'error');
      setStatus('Erro');
      return;
    }

    addMessage(message, 'user');
    messageInput.value = '';
    
    sendBtn.disabled = true;
    setStatus('Enviando...');

    try {
      // Validar licença
      const response = await chrome.runtime.sendMessage({ action: 'validateLicense' });
      
      if (!response.success || !response.valid) {
        throw new Error('Licença inválida. Por favor, ative sua licença.');
      }

      // NOVA IMPLEMENTAÇÃO: Injeção via DOM
      const success = injectMessageToLovable(message);
      
      if (success) {
        addMessage('✅ Mensagem enviada com sucesso!', 'success');
        setStatus('Enviado');
        
        // Calcular tokens economizados (estimativa: 4 chars = 1 token)
        const tokensSaved = message.length / 4;
        
        // Atualizar estatísticas localmente
        const stats = await chrome.storage.local.get(['chatlove_stats']);
        const currentStats = stats.chatlove_stats || { tokens_saved: 0, requests_count: 0 };
        currentStats.tokens_saved += tokensSaved;
        currentStats.requests_count += 1;
        await chrome.storage.local.set({ chatlove_stats: currentStats });
        
        tokensSaved.textContent = currentStats.tokens_saved.toFixed(2);
        addMessage(`💰 +${tokensSaved.toFixed(2)} tokens economizados!`, 'success');
      } else {
        addMessage('❌ Erro: Não foi possível enviar a mensagem. Verifique se você está em um projeto do Lovable.', 'error');
        setStatus('Falha');
      }

    } catch (error) {
      console.error('[ChatLove] Error:', error);
      addMessage(`❌ Erro: ${error.message}`, 'error');
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

console.log('♥ ChatLove loaded!');
