/**
 * Lovable API Scraper
 * Script automatizado para capturar e documentar a API do Lovable
 * 
 * Uso: node lovable-scraper.js
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Configurações
const CONFIG = {
  headless: false,  // Modo visível para acompanhar
  devtools: true,   // DevTools aberto
  captureDir: './captures',
  outputFile: 'lovable-capture.json',
  docsFile: 'lovable-api-docs.md'
};

// Cores para console
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Armazenamento de capturas
const captures = {
  requests: [],
  responses: [],
  cookies: [],
  localStorage: [],
  sessionStorage: [],
  websockets: []
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function waitForEnter(message = '⏸️  Pressione ENTER para continuar...') {
  return new Promise(resolve => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    rl.question(`${colors.yellow}${message}${colors.reset}\n`, () => {
      rl.close();
      resolve();
    });
  });
}

function saveCaptures() {
  // Criar diretório se não existir
  if (!fs.existsSync(CONFIG.captureDir)) {
    fs.mkdirSync(CONFIG.captureDir, { recursive: true });
  }

  // Salvar JSON completo
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = path.join(CONFIG.captureDir, `capture-${timestamp}.json`);
  
  fs.writeFileSync(filename, JSON.stringify(captures, null, 2));
  log(`✅ Dados salvos em: ${filename}`, 'green');
  
  return filename;
}

function filterLovableRequests(url) {
  return url.includes('lovable.dev') || 
         url.includes('api.lovable') ||
         url.includes('supabase');
}

// =============================================================================
// MAIN SCRAPER
// =============================================================================

async function scrapeLovableAPI() {
  log('═══════════════════════════════════════════════════════', 'cyan');
  log('🔍 LOVABLE API SCRAPER', 'bright');
  log('═══════════════════════════════════════════════════════', 'cyan');
  log('');

  // 1. Iniciar navegador
  log('📍 Iniciando navegador...', 'blue');
  const browser = await puppeteer.launch({
    headless: CONFIG.headless,
    devtools: CONFIG.devtools,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-web-security',
      '--disable-features=IsolateOrigins,site-per-process'
    ]
  });

  const page = await browser.newPage();
  
  // Configurar viewport
  await page.setViewport({ width: 1920, height: 1080 });

  // 2. Interceptar requisições
  log('📡 Configurando interceptação de rede...', 'blue');
  
  await page.setRequestInterception(true);
  
  page.on('request', request => {
    const url = request.url();
    
    if (filterLovableRequests(url)) {
      captures.requests.push({
        timestamp: new Date().toISOString(),
        url: url,
        method: request.method(),
        headers: request.headers(),
        postData: request.postData(),
        resourceType: request.resourceType()
      });
      
      log(`📤 REQUEST: ${request.method()} ${url.substring(0, 80)}...`, 'magenta');
    }
    
    request.continue();
  });

  page.on('response', async response => {
    const url = response.url();
    
    if (filterLovableRequests(url)) {
      try {
        const headers = response.headers();
        let body = null;
        
        // Tentar capturar body (pode falhar para alguns tipos)
        try {
          body = await response.text();
        } catch (e) {
          body = '[Binary or unavailable]';
        }
        
        captures.responses.push({
          timestamp: new Date().toISOString(),
          url: url,
          status: response.status(),
          statusText: response.statusText(),
          headers: headers,
          body: body
        });
        
        log(`📥 RESPONSE: ${response.status()} ${url.substring(0, 80)}...`, 'cyan');
      } catch (error) {
        log(`⚠️  Erro ao capturar response: ${error.message}`, 'yellow');
      }
    }
  });

  // 3. Capturar console logs
  page.on('console', msg => {
    if (msg.text().includes('lovable') || msg.text().includes('api')) {
      log(`🖥️  CONSOLE: ${msg.text()}`, 'yellow');
    }
  });

  // 4. Navegar para Lovable
  log('');
  log('📍 Acessando Lovable.dev...', 'blue');
  await page.goto('https://lovable.dev', { waitUntil: 'networkidle2' });
  
  // Capturar cookies iniciais
  const initialCookies = await page.cookies();
  captures.cookies.push({
    timestamp: new Date().toISOString(),
    stage: 'initial',
    cookies: initialCookies
  });

  // 5. PAUSE - Login
  log('');
  log('═══════════════════════════════════════════════════════', 'yellow');
  log('⏸️  ETAPA 1: LOGIN', 'bright');
  log('═══════════════════════════════════════════════════════', 'yellow');
  log('Por favor, faça login manualmente no navegador.', 'yellow');
  await waitForEnter();

  // Capturar cookies após login
  const loginCookies = await page.cookies();
  captures.cookies.push({
    timestamp: new Date().toISOString(),
    stage: 'after_login',
    cookies: loginCookies
  });
  
  // Capturar localStorage e sessionStorage
  const storage = await page.evaluate(() => {
    return {
      localStorage: { ...localStorage },
      sessionStorage: { ...sessionStorage }
    };
  });
  captures.localStorage.push(storage.localStorage);
  captures.sessionStorage.push(storage.sessionStorage);

  log('✅ Login detectado!', 'green');

  // 6. Navegar para projetos
  log('');
  log('📍 Navegando para lista de projetos...', 'blue');
  await page.goto('https://lovable.dev/projects', { waitUntil: 'networkidle2' });
  await page.waitForTimeout(2000);

  // 7. PAUSE - Criar projeto
  log('');
  log('═══════════════════════════════════════════════════════', 'yellow');
  log('⏸️  ETAPA 2: CRIAR PROJETO DE TESTE', 'bright');
  log('═══════════════════════════════════════════════════════', 'yellow');
  log('Por favor, crie um novo projeto de teste.', 'yellow');
  log('Pode ser qualquer projeto simples.', 'yellow');
  await waitForEnter();

  log('✅ Projeto criado!', 'green');

  // 8. Aguardar chat carregar
  log('');
  log('📍 Aguardando interface de chat carregar...', 'blue');
  
  try {
    await page.waitForSelector('[contenteditable="true"]', { timeout: 15000 });
    log('✅ Chat detectado!', 'green');
  } catch (error) {
    log('⚠️  Chat não detectado automaticamente. Continue manualmente.', 'yellow');
  }

  // 9. PAUSE - Enviar mensagens
  log('');
  log('═══════════════════════════════════════════════════════', 'yellow');
  log('⏸️  ETAPA 3: ENVIAR MENSAGENS DE TESTE', 'bright');
  log('═══════════════════════════════════════════════════════', 'yellow');
  log('Por favor, envie algumas mensagens de teste:', 'yellow');
  log('  1. "Create a hello world button"', 'yellow');
  log('  2. "Change button color to red"', 'yellow');
  log('  3. "Add a counter that increments on click"', 'yellow');
  log('', 'yellow');
  log('Aguarde as respostas da IA entre cada mensagem.', 'yellow');
  await waitForEnter();

  log('✅ Mensagens enviadas!', 'green');

  // 10. PAUSE - Explorar recursos
  log('');
  log('═══════════════════════════════════════════════════════', 'yellow');
  log('⏸️  ETAPA 4: EXPLORAR RECURSOS (OPCIONAL)', 'bright');
  log('═══════════════════════════════════════════════════════', 'yellow');
  log('Explore outros recursos se desejar:', 'yellow');
  log('  - Upload de arquivos', 'yellow');
  log('  - Configurações do projeto', 'yellow');
  log('  - Preview/Deploy', 'yellow');
  log('  - Qualquer outro recurso interessante', 'yellow');
  await waitForEnter();

  // 11. Captura final
  log('');
  log('📍 Capturando estado final...', 'blue');
  
  const finalCookies = await page.cookies();
  captures.cookies.push({
    timestamp: new Date().toISOString(),
    stage: 'final',
    cookies: finalCookies
  });

  const finalStorage = await page.evaluate(() => {
    return {
      localStorage: { ...localStorage },
      sessionStorage: { ...sessionStorage }
    };
  });
  captures.localStorage.push(finalStorage.localStorage);
  captures.sessionStorage.push(finalStorage.sessionStorage);

  // 12. Salvar dados
  log('');
  log('💾 Salvando dados capturados...', 'blue');
  const filename = saveCaptures();

  // 13. Estatísticas
  log('');
  log('═══════════════════════════════════════════════════════', 'green');
  log('✅ CAPTURA COMPLETA!', 'bright');
  log('═══════════════════════════════════════════════════════', 'green');
  log(`📊 Estatísticas:`, 'cyan');
  log(`   - Requisições capturadas: ${captures.requests.length}`, 'cyan');
  log(`   - Respostas capturadas: ${captures.responses.length}`, 'cyan');
  log(`   - Cookies capturados: ${captures.cookies.length} snapshots`, 'cyan');
  log(`   - Arquivo salvo: ${filename}`, 'cyan');
  log('');
  log('📝 Próximo passo: Execute "npm run analyze" para analisar os dados', 'yellow');
  log('');

  // 14. Manter navegador aberto
  log('⏸️  Navegador permanecerá aberto para inspeção manual.', 'yellow');
  await waitForEnter('Pressione ENTER para fechar o navegador e finalizar...');

  await browser.close();
  log('');
  log('👋 Scraper finalizado!', 'green');
}

// =============================================================================
// EXECUTION
// =============================================================================

scrapeLovableAPI().catch(error => {
  console.error('❌ Erro fatal:', error);
  process.exit(1);
});
