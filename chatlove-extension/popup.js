/**
 * ChatLove - Popup Script
 * Handles license activation and dashboard
 */

// Elements
const loading = document.getElementById('loading');
const activationForm = document.getElementById('activation-form');
const dashboard = document.getElementById('dashboard');
const messageContainer = document.getElementById('message-container');
const activateForm = document.getElementById('activate-form');
const activateBtn = document.getElementById('activate-btn');
const logoutBtn = document.getElementById('logout-btn');
const usernameInput = document.getElementById('username');
const licenseKeyInput = document.getElementById('license-key');
const userNameDisplay = document.getElementById('user-name');
const tokensSavedDisplay = document.getElementById('tokens-saved');
const requestsCountDisplay = document.getElementById('requests-count');

// =============================================================================
// INITIALIZATION
// =============================================================================

async function init() {
  // Check if already activated
  const response = await chrome.runtime.sendMessage({ action: 'validateLicense' });
  
  if (response.success && response.valid) {
    // Show dashboard
    await loadDashboard();
  } else {
    // Show activation form
    showActivationForm();
  }
}

// =============================================================================
// ACTIVATION FORM
// =============================================================================

function showActivationForm() {
  loading.classList.add('hidden');
  activationForm.classList.remove('hidden');
  dashboard.classList.add('hidden');
}

activateForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const username = usernameInput.value.trim();
  const licenseKey = licenseKeyInput.value.trim().toUpperCase();
  
  if (!username || !licenseKey) {
    showMessage('Preencha todos os campos', 'error');
    return;
  }
  
  // Disable button
  activateBtn.disabled = true;
  activateBtn.textContent = 'Ativando...';
  
  try {
    const response = await chrome.runtime.sendMessage({
      action: 'activateLicense',
      data: { username, licenseKey }
    });
    
    if (response.success) {
      showMessage('Licença ativada com sucesso!', 'success');
      
      // Smooth transition to dashboard
      setTimeout(() => {
        activationForm.style.opacity = '0';
        activationForm.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
          loadDashboard();
          dashboard.style.opacity = '0';
          dashboard.style.transform = 'translateY(20px)';
          
          setTimeout(() => {
            dashboard.style.transition = 'all 0.5s ease';
            dashboard.style.opacity = '1';
            dashboard.style.transform = 'translateY(0)';
          }, 50);
        }, 300);
      }, 1000);
    } else {
      showMessage(response.error || 'Erro ao ativar licença', 'error');
      activateBtn.disabled = false;
      activateBtn.textContent = 'Ativar Licença';
    }
  } catch (error) {
    showMessage('Erro de conexão com o servidor', 'error');
    activateBtn.disabled = false;
    activateBtn.textContent = 'Ativar Licença';
  }
});

// =============================================================================
// DASHBOARD
// =============================================================================

async function loadDashboard() {
  loading.classList.add('hidden');
  activationForm.classList.add('hidden');
  dashboard.classList.remove('hidden');
  
  // Load user data
  const user = await chrome.storage.local.get(['chatlove_user']);
  if (user.chatlove_user) {
    userNameDisplay.textContent = user.chatlove_user.name;
  }
  
  // Load stats
  const stats = await chrome.storage.local.get(['chatlove_stats']);
  if (stats.chatlove_stats) {
    tokensSavedDisplay.textContent = stats.chatlove_stats.tokens_saved.toFixed(2);
    requestsCountDisplay.textContent = stats.chatlove_stats.requests_count;
  }
}

logoutBtn.addEventListener('click', async () => {
  if (confirm('Tem certeza que deseja sair?')) {
    await chrome.runtime.sendMessage({ action: 'logout' });
    await chrome.storage.local.remove(['chatlove_stats']);
    showActivationForm();
    usernameInput.value = '';
    licenseKeyInput.value = '';
  }
});

// =============================================================================
// HELPERS
// =============================================================================

function showMessage(text, type = 'error') {
  messageContainer.innerHTML = `
    <div class="message ${type}">
      ${text}
    </div>
  `;
  
  setTimeout(() => {
    messageContainer.innerHTML = '';
  }, 5000);
}

// Format license key input
licenseKeyInput.addEventListener('input', (e) => {
  let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
  
  // Add dashes
  if (value.length > 4) {
    value = value.match(/.{1,4}/g).join('-');
  }
  
  e.target.value = value.substring(0, 19); // XXXX-XXXX-XXXX-XXXX
});

// Initialize
init();
