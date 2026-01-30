/**
 * Lovable API Analyzer
 * Analisa os dados capturados e gera documentação
 * 
 * Uso: node analyze-capture.js [arquivo-de-captura.json]
 */

const fs = require('fs');
const path = require('path');

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
// ANÁLISE DE DADOS
// =============================================================================

function analyzeCapture(captureData) {
  const analysis = {
    endpoints: new Map(),
    methods: new Set(),
    headers: new Map(),
    payloadStructures: [],
    responseStructures: [],
    cookies: [],
    parameters: new Set(),
    authentication: {
      type: null,
      tokens: []
    }
  };

  // Analisar requisições
  captureData.requests.forEach(req => {
    try {
      const url = new URL(req.url);
      const endpoint = url.pathname;
      
      // Agrupar por endpoint
      if (!analysis.endpoints.has(endpoint)) {
        analysis.endpoints.set(endpoint, {
          methods: new Set(),
          examples: [],
          parameters: new Set()
        });
      }
      
      const endpointData = analysis.endpoints.get(endpoint);
      endpointData.methods.add(req.method);
      
      // Adicionar exemplo
      if (endpointData.examples.length < 3) {
        endpointData.examples.push({
          method: req.method,
          headers: req.headers,
          postData: req.postData
        });
      }
      
      // Extrair parâmetros da URL
      url.searchParams.forEach((value, key) => {
        endpointData.parameters.add(key);
        analysis.parameters.add(key);
      });
      
      // Analisar headers
      Object.keys(req.headers).forEach(header => {
        if (!analysis.headers.has(header)) {
          analysis.headers.set(header, new Set());
        }
        analysis.headers.get(header).add(req.headers[header]);
      });
      
      // Detectar autenticação
      if (req.headers.authorization) {
        const authValue = req.headers.authorization;
        if (authValue.startsWith('Bearer ')) {
          analysis.authentication.type = 'Bearer Token';
          analysis.authentication.tokens.push(authValue.substring(7, 50) + '...');
        }
      }
      
      // Analisar payload
      if (req.postData) {
        try {
          const payload = JSON.parse(req.postData);
          analysis.payloadStructures.push({
            endpoint: endpoint,
            method: req.method,
            structure: getObjectStructure(payload)
          });
        } catch (e) {
          // Não é JSON
        }
      }
      
      analysis.methods.add(req.method);
    } catch (e) {
      // URL inválida ou erro de parsing
    }
  });

  // Analisar respostas
  captureData.responses.forEach(res => {
    try {
      const url = new URL(res.url);
      const endpoint = url.pathname;
      
      if (res.body && res.body !== '[Binary or unavailable]') {
        try {
          const body = JSON.parse(res.body);
          analysis.responseStructures.push({
            endpoint: endpoint,
            status: res.status,
            structure: getObjectStructure(body)
          });
        } catch (e) {
          // Não é JSON
        }
      }
    } catch (e) {
      // URL inválida
    }
  });

  // Analisar cookies
  if (captureData.cookies && captureData.cookies.length > 0) {
    const loginCookies = captureData.cookies.find(c => c.stage === 'after_login');
    if (loginCookies) {
      analysis.cookies = loginCookies.cookies.map(c => ({
        name: c.name,
        domain: c.domain,
        secure: c.secure,
        httpOnly: c.httpOnly
      }));
    }
  }

  return analysis;
}

function getObjectStructure(obj, depth = 0, maxDepth = 3) {
  if (depth > maxDepth) return '...';
  
  if (Array.isArray(obj)) {
    if (obj.length === 0) return '[]';
    return `[${getObjectStructure(obj[0], depth + 1, maxDepth)}]`;
  }
  
  if (typeof obj === 'object' && obj !== null) {
    const structure = {};
    for (const key in obj) {
      const value = obj[key];
      if (typeof value === 'object') {
        structure[key] = getObjectStructure(value, depth + 1, maxDepth);
      } else {
        structure[key] = typeof value;
      }
    }
    return structure;
  }
  
  return typeof obj;
}

// =============================================================================
// GERAÇÃO DE DOCUMENTAÇÃO
// =============================================================================

function generateDocumentation(analysis) {
  let doc = '';
  
  doc += '# 📚 LOVABLE API - DOCUMENTAÇÃO COMPLETA\n\n';
  doc += `> Documentação gerada automaticamente em ${new Date().toLocaleString('pt-BR')}\n\n`;
  doc += '---\n\n';
  
  // Autenticação
  doc += '## 🔐 AUTENTICAÇÃO\n\n';
  if (analysis.authentication.type) {
    doc += `**Tipo:** ${analysis.authentication.type}\n\n`;
    doc += '**Header:**\n```\n';
    doc += 'Authorization: Bearer {token}\n';
    doc += '```\n\n';
  }
  
  // Cookies importantes
  if (analysis.cookies.length > 0) {
    doc += '**Cookies Necessários:**\n\n';
    analysis.cookies.forEach(cookie => {
      doc += `- **${cookie.name}**\n`;
      doc += `  - Domain: ${cookie.domain}\n`;
      doc += `  - Secure: ${cookie.secure}\n`;
      doc += `  - HttpOnly: ${cookie.httpOnly}\n\n`;
    });
  }
  
  doc += '---\n\n';
  
  // Endpoints
  doc += '## 🌐 ENDPOINTS DESCOBERTOS\n\n';
  doc += `Total de endpoints únicos: **${analysis.endpoints.size}**\n\n`;
  
  const sortedEndpoints = Array.from(analysis.endpoints.entries()).sort((a, b) => 
    a[0].localeCompare(b[0])
  );
  
  sortedEndpoints.forEach(([endpoint, data]) => {
    doc += `### \`${endpoint}\`\n\n`;
    
    // Métodos
    doc += '**Métodos:** ';
    doc += Array.from(data.methods).map(m => `\`${m}\``).join(', ');
    doc += '\n\n';
    
    // Parâmetros
    if (data.parameters.size > 0) {
      doc += '**Parâmetros de URL:**\n';
      Array.from(data.parameters).forEach(param => {
        doc += `- \`${param}\`\n`;
      });
      doc += '\n';
    }
    
    // Exemplos
    if (data.examples.length > 0) {
      doc += '**Exemplos de Requisição:**\n\n';
      data.examples.forEach((example, idx) => {
        doc += `#### Exemplo ${idx + 1}: ${example.method}\n\n`;
        
        // Headers importantes
        const importantHeaders = ['authorization', 'content-type', 'x-client-git-sha'];
        doc += '```http\n';
        doc += `${example.method} ${endpoint}\n`;
        importantHeaders.forEach(header => {
          if (example.headers[header]) {
            doc += `${header}: ${example.headers[header].substring(0, 60)}...\n`;
          }
        });
        doc += '```\n\n';
        
        // Payload
        if (example.postData) {
          try {
            const payload = JSON.parse(example.postData);
            doc += '**Payload:**\n```json\n';
            doc += JSON.stringify(payload, null, 2);
            doc += '\n```\n\n';
          } catch (e) {
            doc += '**Payload:** (não-JSON)\n\n';
          }
        }
      });
    }
    
    doc += '---\n\n';
  });
  
  // Estruturas de Payload
  if (analysis.payloadStructures.length > 0) {
    doc += '## 📦 ESTRUTURAS DE PAYLOAD\n\n';
    
    const uniqueStructures = new Map();
    analysis.payloadStructures.forEach(ps => {
      const key = `${ps.method} ${ps.endpoint}`;
      if (!uniqueStructures.has(key)) {
        uniqueStructures.set(key, ps);
      }
    });
    
    uniqueStructures.forEach((ps, key) => {
      doc += `### ${key}\n\n`;
      doc += '```javascript\n';
      doc += JSON.stringify(ps.structure, null, 2);
      doc += '\n```\n\n';
    });
    
    doc += '---\n\n';
  }
  
  // Estruturas de Response
  if (analysis.responseStructures.length > 0) {
    doc += '## 📥 ESTRUTURAS DE RESPOSTA\n\n';
    
    const uniqueResponses = new Map();
    analysis.responseStructures.forEach(rs => {
      const key = `${rs.endpoint} (${rs.status})`;
      if (!uniqueResponses.has(key)) {
        uniqueResponses.set(key, rs);
      }
    });
    
    uniqueResponses.forEach((rs, key) => {
      doc += `### ${key}\n\n`;
      doc += '```javascript\n';
      doc += JSON.stringify(rs.structure, null, 2);
      doc += '\n```\n\n';
    });
    
    doc += '---\n\n';
  }
  
  // Headers comuns
  doc += '## 📋 HEADERS COMUNS\n\n';
  const importantHeaders = ['authorization', 'content-type', 'user-agent', 'origin', 'referer'];
  importantHeaders.forEach(header => {
    if (analysis.headers.has(header)) {
      const values = Array.from(analysis.headers.get(header));
      doc += `### \`${header}\`\n\n`;
      values.forEach(value => {
        doc += `- \`${value.substring(0, 100)}${value.length > 100 ? '...' : ''}\`\n`;
      });
      doc += '\n';
    }
  });
  
  doc += '---\n\n';
  
  // Resumo
  doc += '## 📊 RESUMO\n\n';
  doc += `- **Total de Endpoints:** ${analysis.endpoints.size}\n`;
  doc += `- **Métodos HTTP:** ${Array.from(analysis.methods).join(', ')}\n`;
  doc += `- **Tipo de Autenticação:** ${analysis.authentication.type || 'Não detectado'}\n`;
  doc += `- **Cookies Importantes:** ${analysis.cookies.length}\n`;
  doc += `- **Parâmetros Únicos:** ${analysis.parameters.size}\n\n`;
  
  doc += '---\n\n';
  doc += '*Documentação gerada por Lovable API Analyzer*\n';
  
  return doc;
}

// =============================================================================
// MAIN
// =============================================================================

function main() {
  log('═══════════════════════════════════════════════════════', 'cyan');
  log('📊 LOVABLE API ANALYZER', 'bright');
  log('═══════════════════════════════════════════════════════', 'cyan');
  log('');

  // Encontrar arquivo de captura mais recente
  const capturesDir = './captures';
  
  if (!fs.existsSync(capturesDir)) {
    log('❌ Diretório de capturas não encontrado!', 'red');
    log('Execute primeiro: npm run scrape', 'yellow');
    process.exit(1);
  }

  const files = fs.readdirSync(capturesDir)
    .filter(f => f.startsWith('capture-') && f.endsWith('.json'))
    .sort()
    .reverse();

  if (files.length === 0) {
    log('❌ Nenhum arquivo de captura encontrado!', 'red');
    log('Execute primeiro: npm run scrape', 'yellow');
    process.exit(1);
  }

  const captureFile = path.join(capturesDir, files[0]);
  log(`📂 Analisando: ${captureFile}`, 'blue');
  log('');

  // Carregar dados
  const captureData = JSON.parse(fs.readFileSync(captureFile, 'utf8'));
  
  log(`📊 Dados carregados:`, 'cyan');
  log(`   - Requisições: ${captureData.requests.length}`, 'cyan');
  log(`   - Respostas: ${captureData.responses.length}`, 'cyan');
  log(`   - Cookies: ${captureData.cookies.length} snapshots`, 'cyan');
  log('');

  // Analisar
  log('🔍 Analisando dados...', 'blue');
  const analysis = analyzeCapture(captureData);
  
  log('');
  log('✅ Análise completa!', 'green');
  log('');
  
  // Exibir resumo
  log('═══════════════════════════════════════════════════════', 'green');
  log('📊 RESUMO DA ANÁLISE', 'bright');
  log('═══════════════════════════════════════════════════════', 'green');
  log('');
  log(`🌐 Endpoints descobertos: ${analysis.endpoints.size}`, 'cyan');
  log(`📋 Métodos HTTP: ${Array.from(analysis.methods).join(', ')}`, 'cyan');
  log(`🔐 Autenticação: ${analysis.authentication.type || 'Não detectado'}`, 'cyan');
  log(`🍪 Cookies importantes: ${analysis.cookies.length}`, 'cyan');
  log(`📦 Estruturas de payload: ${analysis.payloadStructures.length}`, 'cyan');
  log(`📥 Estruturas de resposta: ${analysis.responseStructures.length}`, 'cyan');
  log('');
  
  // Listar endpoints
  log('🌐 ENDPOINTS:', 'yellow');
  Array.from(analysis.endpoints.entries()).forEach(([endpoint, data]) => {
    const methods = Array.from(data.methods).join(', ');
    log(`   ${methods.padEnd(20)} ${endpoint}`, 'magenta');
  });
  log('');
  
  // Gerar documentação
  log('📝 Gerando documentação...', 'blue');
  const documentation = generateDocumentation(analysis);
  
  const docsFile = path.join(capturesDir, 'lovable-api-docs.md');
  fs.writeFileSync(docsFile, documentation);
  
  log(`✅ Documentação salva em: ${docsFile}`, 'green');
  log('');
  
  // Salvar análise JSON
  const analysisFile = path.join(capturesDir, 'analysis.json');
  fs.writeFileSync(analysisFile, JSON.stringify({
    endpoints: Array.from(analysis.endpoints.entries()).map(([k, v]) => ({
      endpoint: k,
      methods: Array.from(v.methods),
      parameters: Array.from(v.parameters),
      examples: v.examples
    })),
    authentication: analysis.authentication,
    cookies: analysis.cookies,
    payloadStructures: analysis.payloadStructures,
    responseStructures: analysis.responseStructures
  }, null, 2));
  
  log(`✅ Análise JSON salva em: ${analysisFile}`, 'green');
  log('');
  
  log('═══════════════════════════════════════════════════════', 'green');
  log('✅ ANÁLISE COMPLETA!', 'bright');
  log('═══════════════════════════════════════════════════════', 'green');
  log('');
  log('📖 Próximos passos:', 'yellow');
  log('   1. Revisar a documentação gerada', 'yellow');
  log('   2. Identificar recursos para implementar no ChatLove', 'yellow');
  log('   3. Testar endpoints descobertos', 'yellow');
  log('');
}

main();
