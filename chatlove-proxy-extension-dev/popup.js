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
    console.log('🔄 Validando licença:', licenseKey);
    
    // Validate license with backend
    const response = await fetch('https://chat.trafficai.cloud/api/validate-license', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        license_key: licenseKey
      })
    });
    
    console.log('📡 Response status:', response.status);
    
    if (!response.ok) {
      showStatus('Erro ao conectar com o backend. Status: ' + response.status, 'error');
      return;
    }
    
    const data = await response.json();
    console.log('📦 Response data:', data);
    
    if (data.success && data.valid) {
      // License is valid, save it
      console.log('✅ Licença válida! Salvando...');
      
      await chrome.storage.local.set({ 
        userName: userName,
        licenseKey: licenseKey,
        certificateAccepted: true  // Marcar certificado como aceito
      });
      
      console.log('💾 Licença salva no storage');
      
      showStatus('Licença ativada com sucesso! ✅', 'success');
      
      // Não recarregar automaticamente - deixar usuário decidir
      setTimeout(() => {
        showStatus('Licença ativa! Abra um projeto no Lovable para usar.', 'success');
      }, 2000);
    } else {
      // Mostrar mensagem específica do backend
      console.log('❌ Licença inválida:', data.message);
      showStatus(data.message || 'Licença inválida ou inativa.', 'error');
    }
  } catch (error) {
    console.error('Error validating license:', error);
    
    // Detectar erro de certificado e abrir página de instruções
    if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
      // Verificar se já abriu instruções antes
      chrome.storage.local.get(['certificateAccepted'], (result) => {
        if (!result.certificateAccepted) {
          // Primeira vez - abrir instruções
          showStatus('Abrindo página de configuração...', 'info');
          
          chrome.tabs.create({ 
            url: 'https://chat.trafficai.cloud',
            active: true 
          });
          
          // Marcar como aceito
          chrome.storage.local.set({ certificateAccepted: true });
          
          setTimeout(() => {
            showStatus('Siga as instruções na aba aberta e tente novamente.', 'info');
          }, 2000);
        } else {
          // Já aceitou certificado - erro real
          showStatus('Erro ao conectar: ' + error.message, 'error');
        }
      });
    } else {
      showStatus('Erro: Backend não está rodando. Inicie: python main.py', 'error');
    }
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
