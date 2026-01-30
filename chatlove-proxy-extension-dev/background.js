/**
 * ChatLove Proxy - Background Script
 * Responsável por capturar cookies (content scripts não têm acesso)
 */

// Listener para mensagens do content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getCookie') {
    // Capturar cookie do Lovable
    chrome.cookies.get(
      {
        url: "https://lovable.dev",
        name: "lovable-session-id.id"
      },
      (cookie) => {
        if (cookie && cookie.value) {
          console.log('[ChatLove Background] Cookie capturado:', cookie.value.substring(0, 50) + '...');
          sendResponse({ cookie: cookie.value });
        } else {
          console.error('[ChatLove Background] Cookie não encontrado');
          sendResponse({ cookie: null });
        }
      }
    );
    
    // Retornar true para indicar que a resposta será assíncrona
    return true;
  }
});

console.log('[ChatLove Background] Background script loaded');
