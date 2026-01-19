/**
 * ChatLove Proxy - Popup Script
 * Gerencia ativação de licença
 */

const userNameInput = document.getElementById('userName');
const licenseInput = document.getElementById('licenseKey');
const activateBtn = document.getElementById('activateBtn');
const statusEl = document.getElementById('status');

// Load saved data on popup open
chrome.storage.local.get(['userName', 'licenseKey'], (result) => {
  if (result.userName) {
    userNameInput.value = result.userName;
  }
  if (result.licenseKey) {
    licenseInput.value = result.licenseKey;
    showStatus('Licença já ativada! Abra um projeto no Lovable.', 'success');
  }
});

// Activate button click
activateBtn.addEventListener('click', async () => {
  const userName = userNameInput.value.trim();
  const licenseKey = licenseInput.value.trim();
  
  if (!userName) {
    showStatus('Digite seu nome', 'error');
    return;
  }
  
  if (!licenseKey) {
    showStatus('Digite uma chave de licença', 'error');
    return;
  }
  
  activateBtn.disabled = true;
  showStatus('Validando licença...', 'info');
  
  try {
    // Save user name and license key
    await chrome.storage.local.set({ 
      userName: userName,
      licenseKey: licenseKey 
    });
    
    // Test connection with backend
    const response = await fetch('http://127.0.0.1:8001/health');
    
    if (response.ok) {
      showStatus('✅ Licença ativada! Abra um projeto no Lovable.', 'success');
    } else {
      showStatus('⚠️ Licença salva, mas backend não está respondendo. Inicie o backend.', 'error');
    }
  } catch (error) {
    // Save anyway, backend might not be running yet
    showStatus('⚠️ Licença salva, mas backend não está rodando. Inicie: python main.py', 'error');
  } finally {
    activateBtn.disabled = false;
  }
});

// Enter to activate
licenseInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    activateBtn.click();
  }
});

function showStatus(message, type) {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.style.display = 'block';
}
