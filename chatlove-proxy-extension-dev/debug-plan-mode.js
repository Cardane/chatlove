/**
 * Script para investigar como ativar o modo Plan da Lovable
 * Execute no console do navegador (F12) quando estiver no projeto Lovable
 */

console.log('🔍 Investigando modo Plan da Lovable...');

// 1. Procurar por elementos relacionados ao modo Chat/Plan
function findChatModeElements() {
  console.log('\n📋 Procurando elementos de modo Chat/Plan:');
  
  const selectors = [
    '[data-testid*="chat"]',
    '[data-testid*="plan"]',
    '[class*="chat"]',
    '[class*="plan"]',
    'button:contains("Chat")',
    'button:contains("Plan")',
    '[role="tab"]',
    '[role="tabpanel"]'
  ];
  
  selectors.forEach(selector => {
    try {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        console.log(`✅ Encontrado: ${selector}`, elements);
        elements.forEach((el, i) => {
          console.log(`  [${i}] Text: "${el.textContent?.trim()}"`, el);
        });
      }
    } catch (e) {
      // Selector inválido, ignorar
    }
  });
}

// 2. Interceptar cliques para ver o que acontece quando muda de modo
function interceptClicks() {
  console.log('\n🖱️ Interceptando cliques...');
  
  document.addEventListener('click', function(event) {
    const element = event.target;
    const text = element.textContent?.trim();
    
    if (text && (text.includes('Chat') || text.includes('Plan') || text.includes('Builder'))) {
      console.log('🎯 Clique interceptado:', {
        element: element,
        text: text,
        classes: element.className,
        dataTestId: element.getAttribute('data-testid'),
        parent: element.parentElement
      });
    }
  }, true);
}

// 3. Monitorar mudanças na URL ou estado
function monitorStateChanges() {
  console.log('\n🔄 Monitorando mudanças de estado...');
  
  // Observer para mudanças no DOM
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === 1) { // Element node
            const text = node.textContent?.toLowerCase();
            if (text && (text.includes('chat') || text.includes('plan') || text.includes('builder'))) {
              console.log('🆕 Novo elemento relacionado ao modo:', node);
            }
          }
        });
      }
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
  
  // Monitorar mudanças na URL
  let currentUrl = window.location.href;
  setInterval(() => {
    if (window.location.href !== currentUrl) {
      console.log('🔗 URL mudou:', {
        from: currentUrl,
        to: window.location.href
      });
      currentUrl = window.location.href;
    }
  }, 1000);
}

// 4. Procurar por requisições de API relacionadas ao modo
function interceptApiCalls() {
  console.log('\n🌐 Interceptando chamadas de API...');
  
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const [url, options] = args;
    
    if (url.toString().includes('lovable') || url.toString().includes('api')) {
      console.log('📡 API Call:', {
        url: url.toString(),
        method: options?.method || 'GET',
        body: options?.body
      });
    }
    
    const response = await originalFetch(...args);
    
    if (url.toString().includes('chat') || url.toString().includes('plan')) {
      const clonedResponse = response.clone();
      try {
        const data = await clonedResponse.json();
        console.log('📡 API Response:', {
          url: url.toString(),
          status: response.status,
          data: data
        });
      } catch (e) {
        // Não é JSON, ignorar
      }
    }
    
    return response;
  };
}

// 5. Analisar estrutura atual da página
function analyzeCurrentPage() {
  console.log('\n🔍 Analisando estrutura atual:');
  
  // Procurar por tabs ou botões de modo
  const possibleModeButtons = document.querySelectorAll('button, [role="tab"], .tab, [class*="mode"]');
  console.log('🔘 Possíveis botões de modo:', possibleModeButtons);
  
  possibleModeButtons.forEach((btn, i) => {
    if (btn.textContent?.trim()) {
      console.log(`  [${i}] "${btn.textContent.trim()}"`, btn);
    }
  });
  
  // Procurar por indicadores de modo atual
  const activeElements = document.querySelectorAll('.active, [aria-selected="true"], [data-state="active"]');
  console.log('✅ Elementos ativos:', activeElements);
  
  // Verificar se há algum indicador de "Chat" vs "Builder"
  const chatElements = document.querySelectorAll('*');
  const chatRelated = Array.from(chatElements).filter(el => {
    const text = el.textContent?.toLowerCase();
    return text && (text.includes('chat') || text.includes('plan') || text.includes('builder')) && text.length < 50;
  });
  
  console.log('💬 Elementos relacionados a Chat/Plan/Builder:', chatRelated);
}

// 6. Simular clique no modo Chat (se encontrar)
function tryActivateChatMode() {
  console.log('\n🎯 Tentando ativar modo Chat...');
  
  // Procurar por botão "Chat"
  const chatButtons = Array.from(document.querySelectorAll('button, [role="tab"]')).filter(btn => {
    const text = btn.textContent?.trim().toLowerCase();
    return text === 'chat' || text === 'plan';
  });
  
  if (chatButtons.length > 0) {
    console.log('🎯 Encontrados botões de Chat:', chatButtons);
    
    chatButtons.forEach((btn, i) => {
      console.log(`  [${i}] Tentando clicar em: "${btn.textContent.trim()}"`, btn);
      
      // Simular clique
      btn.click();
      
      setTimeout(() => {
        console.log(`  [${i}] Estado após clique:`, {
          classes: btn.className,
          ariaSelected: btn.getAttribute('aria-selected'),
          dataState: btn.getAttribute('data-state')
        });
      }, 500);
    });
  } else {
    console.log('❌ Nenhum botão de Chat encontrado');
  }
}

// Executar todas as análises
function runFullAnalysis() {
  console.log('🚀 Iniciando análise completa do modo Plan/Chat da Lovable...\n');
  
  findChatModeElements();
  analyzeCurrentPage();
  interceptClicks();
  monitorStateChanges();
  interceptApiCalls();
  
  setTimeout(() => {
    tryActivateChatMode();
  }, 2000);
  
  console.log('\n✅ Análise iniciada! Agora:');
  console.log('1. Clique manualmente no botão "Chat" se existir');
  console.log('2. Observe os logs no console');
  console.log('3. Tente enviar uma mensagem em modo Plan');
  console.log('4. Compare as requisições entre Builder e Plan');
}

// Auto-executar
runFullAnalysis();

// Expor funções para uso manual
window.lovableDebug = {
  findElements: findChatModeElements,
  analyzePage: analyzeCurrentPage,
  tryActivateChat: tryActivateChatMode,
  runFull: runFullAnalysis
};

console.log('\n🛠️ Funções disponíveis:');
console.log('- window.lovableDebug.findElements()');
console.log('- window.lovableDebug.analyzePage()');
console.log('- window.lovableDebug.tryActivateChat()');
console.log('- window.lovableDebug.runFull()');