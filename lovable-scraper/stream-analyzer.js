/**
 * Lovable API Stream Analyzer
 * Processa arquivos grandes de captura em streaming
 * Gera múltiplos arquivos organizados por categoria
 * 
 * Uso: node stream-analyzer.js [arquivo-de-captura.json]
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Cores para console
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  red: '\x1b[31m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

// =============================================================================
// CONFIGURAÇÃO
// =============================================================================

const CONFIG = {
  maxExamplesPerEndpoint: 3,
  maxPayloadSize: 50000, // 50KB por payload
  outputDir: './captures/streaming-analysis',
  chunkSize: 1024 * 1024 // 1MB chunks
};

// Parse argumentos
const args = process.argv.slice(2);
const options = {
  only: null,
  maxExamples: CONFIG.maxExamplesPerEndpoint
};

args.forEach(arg => {
  if (arg.startsWith('--only=')) {
    options.only = arg.split('=')[1];
  }
  if (arg.startsWith('--max-examples=')) {
    options.maxExamples = parseInt(arg.split('=')[1]);
  }
});

// =============================================================================
// ESTRUTURAS DE DADOS
// =============================================================================

class StreamAnalyzer {
  constructor() {
    this.stats = {
      totalRequests: 0,
      totalResponses: 0,
      totalCookies: 0,
      processedRequests: 0,
      processedResponses: 0,
      startTime: Date.now()
    };

    this.endpoints = new Map();
    this.authentication = {
      tokens: new Set(),
      cookies: [],
      headers: new Map()
    };

    this.payloadsByEndpoint = new Map();
    this.responsesByEndpoint = new Map();
  }

  // Processa uma requisição
  processRequest(request) {
    this.stats.processedRequests++;

    try {
      const url = new URL(request.url);
      const endpoint = this.normalizeEndpoint(url.pathname);
      const method = request.method;

      // Registrar endpoint
      if (!this.endpoints.has(endpoint)) {
        this.endpoints.set(endpoint, {
          methods: new Set(),
          count: 0,
          parameters: new Set()
        });
      }

      const endpointData = this.endpoints.get(endpoint);
      endpointData.methods.add(method);
      endpointData.count++;

      // Extrair parâmetros
      url.searchParams.forEach((value, key) => {
        endpointData.parameters.add(key);
      });

      // Autenticação
      if (request.headers && request.headers.authorization) {
        const auth = request.headers.authorization;
        if (auth.startsWith('Bearer ')) {
          this.authentication.tokens.add(auth.substring(7, 50) + '...');
        }
      }

      // Headers importantes
      if (request.headers) {
        ['authorization', 'x-client-git-sha', 'x-supabase-api-version'].forEach(header => {
          if (request.headers[header]) {
            if (!this.authentication.headers.has(header)) {
              this.authentication.headers.set(header, new Set());
            }
            this.authentication.headers.get(header).add(request.headers[header]);
          }
        });
      }

      // Payloads
      if (request.postData && method !== 'GET') {
        const key = `${method}-${endpoint}`;
        if (!this.payloadsByEndpoint.has(key)) {
          this.payloadsByEndpoint.set(key, []);
        }

        const payloads = this.payloadsByEndpoint.get(key);
        if (payloads.length < options.maxExamples) {
          try {
            const payload = JSON.parse(request.postData);
            // Limitar tamanho
            const payloadStr = JSON.stringify(payload);
            if (payloadStr.length < CONFIG.maxPayloadSize) {
              payloads.push({
                timestamp: request.timestamp,
                headers: this.extractImportantHeaders(request.headers),
                payload: payload
              });
            }
          } catch (e) {
            // Não é JSON válido
          }
        }
      }
    } catch (e) {
      // URL inválida ou erro de parsing
    }
  }

  // Processa uma resposta
  processResponse(response) {
    this.stats.processedResponses++;

    try {
      const url = new URL(response.url);
      const endpoint = this.normalizeEndpoint(url.pathname);
      const status = response.status;

      const key = `${endpoint}-${status}`;
      if (!this.responsesByEndpoint.has(key)) {
        this.responsesByEndpoint.set(key, []);
      }

      const responses = this.responsesByEndpoint.get(key);
      if (responses.length < options.maxExamples) {
        if (response.body && response.body !== '[Binary or unavailable]') {
          try {
            const body = JSON.parse(response.body);
            const bodyStr = JSON.stringify(body);
            
            // Limitar tamanho
            if (bodyStr.length < CONFIG.maxPayloadSize) {
              responses.push({
                timestamp: response.timestamp,
                status: status,
                headers: this.extractImportantHeaders(response.headers),
                body: body,
                structure: this.getObjectStructure(body)
              });
            } else {
              // Apenas estrutura para responses grandes
              responses.push({
                timestamp: response.timestamp,
                status: status,
                headers: this.extractImportantHeaders(response.headers),
                structure: this.getObjectStructure(body),
                note: 'Body too large - only structure included'
              });
            }
          } catch (e) {
            // Não é JSON
          }
        }
      }
    } catch (e) {
      // URL inválida
    }
  }

  // Processa cookies
  processCookies(cookieSnapshot) {
    this.stats.totalCookies++;

    if (cookieSnapshot.stage === 'after_login' && cookieSnapshot.cookies) {
      this.authentication.cookies = cookieSnapshot.cookies.map(c => ({
        name: c.name,
        domain: c.domain,
        secure: c.secure,
        httpOnly: c.httpOnly,
        sameSite: c.sameSite
      }));
    }
  }

  // Normaliza endpoint (substitui IDs por placeholders)
  normalizeEndpoint(pathname) {
    return pathname
      .replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, '/{uuid}')
      .replace(/\/[0-9a-f]{20,}/gi, '/{id}')
      .replace(/\/\d+/g, '/{id}');
  }

  // Extrai headers importantes
  extractImportantHeaders(headers) {
    if (!headers) return {};
    
    const important = {};
    ['authorization', 'content-type', 'x-client-git-sha', 'x-supabase-api-version'].forEach(key => {
      if (headers[key]) {
        important[key] = headers[key];
      }
    });
    return important;
  }

  // Obtém estrutura de objeto
  getObjectStructure(obj, depth = 0, maxDepth = 3) {
    if (depth > maxDepth) return '...';
    
    if (Array.isArray(obj)) {
      if (obj.length === 0) return '[]';
      return `[${this.getObjectStructure(obj[0], depth + 1, maxDepth)}]`;
    }
    
    if (typeof obj === 'object' && obj !== null) {
      const structure = {};
      for (const key in obj) {
        const value = obj[key];
        if (typeof value === 'object') {
          structure[key] = this.getObjectStructure(value, depth + 1, maxDepth);
        } else {
          structure[key] = typeof value;
        }
      }
      return structure;
    }
    
    return typeof obj;
  }

  // Gera relatório
  generateReport() {
    const duration = ((Date.now() - this.stats.startTime) / 1000).toFixed(2);
    
    let report = '';
    report += '# 📊 LOVABLE API - ANÁLISE EM STREAMING\n\n';
    report += `> Gerado em ${new Date().toLocaleString('pt-BR')}\n\n`;
    report += '---\n\n';

    // Estatísticas
    report += '## 📈 ESTATÍSTICAS\n\n';
    report += `- **Requisições processadas:** ${this.stats.processedRequests}\n`;
    report += `- **Respostas processadas:** ${this.stats.processedResponses}\n`;
    report += `- **Endpoints únicos:** ${this.endpoints.size}\n`;
    report += `- **Tempo de processamento:** ${duration}s\n\n`;
    report += '---\n\n';

    // Autenticação
    report += '## 🔐 AUTENTICAÇÃO\n\n';
    if (this.authentication.tokens.size > 0) {
      report += '**Tipo:** Bearer Token\n\n';
      report += '**Exemplo de Token:**\n```\n';
      report += `Authorization: Bearer ${Array.from(this.authentication.tokens)[0]}\n`;
      report += '```\n\n';
    }

    if (this.authentication.cookies.length > 0) {
      report += '**Cookies Importantes:**\n\n';
      this.authentication.cookies.forEach(cookie => {
        report += `- **${cookie.name}**\n`;
        report += `  - Domain: ${cookie.domain}\n`;
        report += `  - Secure: ${cookie.secure}\n`;
        report += `  - HttpOnly: ${cookie.httpOnly}\n\n`;
      });
    }

    report += '---\n\n';

    // Endpoints
    report += '## 🌐 ENDPOINTS DESCOBERTOS\n\n';
    const sortedEndpoints = Array.from(this.endpoints.entries())
      .sort((a, b) => b[1].count - a[1].count);

    sortedEndpoints.forEach(([endpoint, data]) => {
      const methods = Array.from(data.methods).join(', ');
      report += `### \`${endpoint}\`\n\n`;
      report += `- **Métodos:** ${methods}\n`;
      report += `- **Requisições:** ${data.count}\n`;
      
      if (data.parameters.size > 0) {
        report += `- **Parâmetros:** ${Array.from(data.parameters).join(', ')}\n`;
      }
      
      report += '\n';
    });

    report += '---\n\n';

    // Payloads
    report += '## 📦 PAYLOADS CAPTURADOS\n\n';
    report += `Total de endpoints com payloads: **${this.payloadsByEndpoint.size}**\n\n`;
    this.payloadsByEndpoint.forEach((payloads, key) => {
      report += `- \`${key}\`: ${payloads.length} exemplo(s)\n`;
    });
    report += '\n';
    report += '*Veja arquivos individuais em: `payloads/`*\n\n';
    report += '---\n\n';

    // Responses
    report += '## 📥 RESPONSES CAPTURADAS\n\n';
    report += `Total de endpoints com responses: **${this.responsesByEndpoint.size}**\n\n`;
    this.responsesByEndpoint.forEach((responses, key) => {
      report += `- \`${key}\`: ${responses.length} exemplo(s)\n`;
    });
    report += '\n';
    report += '*Veja arquivos individuais em: `responses/`*\n\n';
    report += '---\n\n';

    // Próximos passos
    report += '## 🚀 PRÓXIMOS PASSOS\n\n';
    report += '1. Revisar endpoints mais usados\n';
    report += '2. Analisar estruturas de payload\n';
    report += '3. Implementar endpoints no ChatLove\n';
    report += '4. Testar autenticação\n\n';
    report += '---\n\n';
    report += '*Análise gerada por Lovable Stream Analyzer*\n';

    return report;
  }
}

// =============================================================================
// PROCESSAMENTO EM STREAMING
// =============================================================================

async function processFileInStreaming(filePath) {
  log('═══════════════════════════════════════════════════════', 'cyan');
  log('📊 LOVABLE STREAM ANALYZER', 'bright');
  log('═══════════════════════════════════════════════════════', 'cyan');
  log('');

  const analyzer = new StreamAnalyzer();

  // Criar diretório de saída (relativo ao script)
  const outputDir = path.join(__dirname, 'captures', 'streaming-analysis');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const payloadsDir = path.join(outputDir, 'payloads');
  const responsesDir = path.join(outputDir, 'responses');
  
  if (!fs.existsSync(payloadsDir)) fs.mkdirSync(payloadsDir, { recursive: true });
  if (!fs.existsSync(responsesDir)) fs.mkdirSync(responsesDir, { recursive: true });

  log(`📂 Processando: ${filePath}`, 'blue');
  log(`📁 Saída: ${CONFIG.outputDir}`, 'blue');
  log('');

  // Ler arquivo completo (para JSON válido precisamos fazer isso)
  log('📖 Carregando arquivo...', 'yellow');
  const fileContent = fs.readFileSync(filePath, 'utf8');
  
  log('🔍 Parsing JSON...', 'yellow');
  const data = JSON.parse(fileContent);

  analyzer.stats.totalRequests = data.requests?.length || 0;
  analyzer.stats.totalResponses = data.responses?.length || 0;

  log('');
  log(`📊 Total de requisições: ${analyzer.stats.totalRequests}`, 'cyan');
  log(`📊 Total de respostas: ${analyzer.stats.totalResponses}`, 'cyan');
  log('');

  // Processar requisições
  if (!options.only || options.only === 'requests' || options.only === 'payloads') {
    log('🔄 Processando requisições...', 'yellow');
    let progress = 0;
    const total = analyzer.stats.totalRequests;
    
    data.requests.forEach((request, idx) => {
      analyzer.processRequest(request);
      
      const newProgress = Math.floor((idx / total) * 100);
      if (newProgress > progress && newProgress % 10 === 0) {
        progress = newProgress;
        process.stdout.write(`\r   Progresso: ${progress}%`);
      }
    });
    
    console.log('');
    log(`✅ ${analyzer.stats.processedRequests} requisições processadas`, 'green');
    log('');
  }

  // Processar respostas
  if (!options.only || options.only === 'responses') {
    log('🔄 Processando respostas...', 'yellow');
    let progress = 0;
    const total = analyzer.stats.totalResponses;
    
    data.responses.forEach((response, idx) => {
      analyzer.processResponse(response);
      
      const newProgress = Math.floor((idx / total) * 100);
      if (newProgress > progress && newProgress % 10 === 0) {
        progress = newProgress;
        process.stdout.write(`\r   Progresso: ${progress}%`);
      }
    });
    
    console.log('');
    log(`✅ ${analyzer.stats.processedResponses} respostas processadas`, 'green');
    log('');
  }

  // Processar cookies
  if (!options.only || options.only === 'auth') {
    if (data.cookies && data.cookies.length > 0) {
      log('🔄 Processando cookies...', 'yellow');
      data.cookies.forEach(snapshot => analyzer.processCookies(snapshot));
      log(`✅ ${analyzer.stats.totalCookies} snapshots de cookies processados`, 'green');
      log('');
    }
  }

  // Salvar resultados
  log('💾 Salvando resultados...', 'blue');
  log('');

  // 1. Summary
  const summary = {
    generatedAt: new Date().toISOString(),
    stats: analyzer.stats,
    endpoints: Array.from(analyzer.endpoints.entries()).map(([endpoint, data]) => ({
      endpoint,
      methods: Array.from(data.methods),
      count: data.count,
      parameters: Array.from(data.parameters)
    }))
  };
  
  fs.writeFileSync(
    path.join(outputDir, 'summary.json'),
    JSON.stringify(summary, null, 2)
  );
  log('✅ summary.json', 'green');

  // 2. Endpoints list
  fs.writeFileSync(
    path.join(outputDir, 'endpoints-list.json'),
    JSON.stringify(summary.endpoints, null, 2)
  );
  log('✅ endpoints-list.json', 'green');

  // 3. Authentication
  const authData = {
    type: analyzer.authentication.tokens.size > 0 ? 'Bearer Token' : 'Unknown',
    tokens: Array.from(analyzer.authentication.tokens),
    cookies: analyzer.authentication.cookies,
    headers: Object.fromEntries(
      Array.from(analyzer.authentication.headers.entries()).map(([k, v]) => [k, Array.from(v)])
    )
  };
  
  fs.writeFileSync(
    path.join(outputDir, 'authentication.json'),
    JSON.stringify(authData, null, 2)
  );
  log('✅ authentication.json', 'green');

  // 4. Payloads
  let payloadCount = 0;
  analyzer.payloadsByEndpoint.forEach((payloads, key) => {
    const filename = key.replace(/\//g, '-').replace(/[{}]/g, '') + '.json';
    fs.writeFileSync(
      path.join(payloadsDir, filename),
      JSON.stringify(payloads, null, 2)
    );
    payloadCount++;
  });
  log(`✅ ${payloadCount} arquivos de payload em payloads/`, 'green');

  // 5. Responses
  let responseCount = 0;
  analyzer.responsesByEndpoint.forEach((responses, key) => {
    const filename = key.replace(/\//g, '-').replace(/[{}]/g, '') + '.json';
    fs.writeFileSync(
      path.join(responsesDir, filename),
      JSON.stringify(responses, null, 2)
    );
    responseCount++;
  });
  log(`✅ ${responseCount} arquivos de response em responses/`, 'green');

  // 6. Report
  const report = analyzer.generateReport();
  fs.writeFileSync(
    path.join(outputDir, 'report.md'),
    report
  );
  log('✅ report.md', 'green');

  log('');
  log('═══════════════════════════════════════════════════════', 'green');
  log('✅ ANÁLISE COMPLETA!', 'bright');
  log('═══════════════════════════════════════════════════════', 'green');
  log('');
  log('📊 RESUMO:', 'yellow');
  log(`   - Endpoints únicos: ${analyzer.endpoints.size}`, 'cyan');
  log(`   - Arquivos de payload: ${payloadCount}`, 'cyan');
  log(`   - Arquivos de response: ${responseCount}`, 'cyan');
  log(`   - Tempo: ${((Date.now() - analyzer.stats.startTime) / 1000).toFixed(2)}s`, 'cyan');
  log('');
  log('📁 Arquivos gerados:', 'yellow');
  log(`   ${outputDir}/`, 'magenta');
  log('');
}

// =============================================================================
// MAIN
// =============================================================================

async function main() {
  // Encontrar arquivo de captura
  const capturesDir = path.join(__dirname, 'captures');
  
  if (!fs.existsSync(capturesDir)) {
    log('❌ Diretório de capturas não encontrado!', 'red');
    process.exit(1);
  }

  const files = fs.readdirSync(capturesDir)
    .filter(f => f.startsWith('capture-') && f.endsWith('.json'))
    .sort()
    .reverse();

  if (files.length === 0) {
    log('❌ Nenhum arquivo de captura encontrado!', 'red');
    process.exit(1);
  }

  const captureFile = path.join(capturesDir, files[0]);
  
  try {
    await processFileInStreaming(captureFile);
  } catch (error) {
    log('', 'reset');
    log('❌ ERRO:', 'red');
    log(error.message, 'red');
    log('', 'reset');
    process.exit(1);
  }
}

main();
