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
    // Validate license with backend
    const response = await fetch('http://127.0.0.1:8000/api/validate-license', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        license_key: licenseKey
      })
    });
    
    if (!response.ok) {
      showStatus('Erro ao conectar com o backend. Verifique se está rodando.', 'error');
      return;
    }
    
    const data = await response.json();
    
    if (data.success && data.valid) {
      // License is valid, save it
      await chrome.storage.local.set({ 
        userName: userName,
        licenseKey: licenseKey 
      });
      showStatus('Licença ativada! Recarregando página...', 'success');
      
      // Reload current tab to inject sidebar
      setTimeout(() => {
        chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
          if (tabs[0]) {
            chrome.tabs.reload(tabs[0].id);
          }
        });
      }, 1000);
    } else {
      // Mostrar mensagem específica do backend
      showStatus(data.message || 'Licença inválida ou inativa.', 'error');
    }
  } catch (error) {
    console.error('Error validating license:', error);
    showStatus('Erro: Backend não está rodando. Inicie: python main.py', 'error');
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
