/**
 * ChatLove - Background Service Worker
 * Handles authentication and session management
 */

// API Configuration
const API_URL = 'http://127.0.0.1:8000';

// =============================================================================
// STORAGE MANAGEMENT
// =============================================================================

async function getStoredToken() {
  const result = await chrome.storage.local.get(['chatlove_token']);
  return result.chatlove_token || null;
}

async function setStoredToken(token) {
  await chrome.storage.local.set({ chatlove_token: token });
}

async function clearStoredToken() {
  await chrome.storage.local.remove(['chatlove_token']);
}

async function getStoredUser() {
  const result = await chrome.storage.local.get(['chatlove_user']);
  return result.chatlove_user || null;
}

async function setStoredUser(user) {
  await chrome.storage.local.set({ chatlove_user: user });
}

// =============================================================================
// FINGERPRINT GENERATION
// =============================================================================

function generateFingerprint() {
  // Service workers don't have access to screen object
  // Use a simple fingerprint based on available data
  return {
    userAgent: navigator.userAgent,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    platform: navigator.platform || 'unknown',
    hardwareConcurrency: navigator.hardwareConcurrency || 0
  };
}

function generateCanvasFingerprint() {
  try {
    const canvas = new OffscreenCanvas(200, 50);
    const ctx = canvas.getContext('2d');
    
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('ChatLove', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('ChatLove', 4, 17);
    
    return canvas.convertToBlob().then(blob => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.readAsDataURL(blob);
      });
    });
  } catch (e) {
    return 'canvas-error';
  }
}

// =============================================================================
// MESSAGE HANDLERS
// =============================================================================

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'activateLicense') {
    handleActivateLicense(request.data)
      .then(sendResponse)
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'validateLicense') {
    handleValidateLicense()
      .then(sendResponse)
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'getToken') {
    getStoredToken()
      .then(token => sendResponse({ success: true, token }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  // getCookies não é mais necessário com DOM injection
  // Mantido para compatibilidade, mas retorna erro
  if (request.action === 'getCookies') {
    sendResponse({ 
      success: false, 
      error: 'getCookies deprecated - using DOM injection instead' 
    });
    return true;
  }
  
  if (request.action === 'logout') {
    handleLogout()
      .then(sendResponse)
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

// =============================================================================
// LICENSE ACTIVATION
// =============================================================================

async function handleActivateLicense(data) {
  const { username, licenseKey } = data;
  
  // Generate fingerprint
  const fingerprint = generateFingerprint();
  
  try {
    const response = await fetch(`${API_URL}/api/license/activate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username,
        license_key: licenseKey,
        fingerprint
      })
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      throw new Error(result.detail || 'Activation failed');
    }
    
    // Store token and user
    await setStoredToken(result.token);
    await setStoredUser(result.user);
    
    return {
      success: true,
      user: result.user
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// =============================================================================
// LICENSE VALIDATION
// =============================================================================

async function handleValidateLicense() {
  const token = await getStoredToken();
  
  if (!token) {
    return { success: false, error: 'No token found' };
  }
  
  const fingerprint = generateFingerprint();
  
  try {
    const response = await fetch(`${API_URL}/api/license/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token,
        fingerprint
      })
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      // Token invalid, clear storage
      await clearStoredToken();
      throw new Error(result.detail || 'Validation failed');
    }
    
    return {
      success: true,
      valid: result.valid
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// =============================================================================
// COOKIE MANAGEMENT
// =============================================================================

async function handleGetCookies(domain) {
  try {
    const cookies = await chrome.cookies.getAll({ domain });
    const sessionCookie = cookies.find(c => c.name === 'lovable-session-id.id');
    
    if (!sessionCookie) {
      return {
        success: false,
        error: 'Session cookie not found'
      };
    }
    
    return {
      success: true,
      sessionCookie: sessionCookie.value
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// =============================================================================
// LOGOUT
// =============================================================================

async function handleLogout() {
  await clearStoredToken();
  await chrome.storage.local.remove(['chatlove_user']);
  
  return { success: true };
}

// =============================================================================
// INITIALIZATION
// =============================================================================

console.log('ChatLove Background Service Worker loaded');
