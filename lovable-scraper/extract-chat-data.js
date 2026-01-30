/**
 * Chat Data Extractor
 * Extrai especificamente dados do endpoint /chat do arquivo de captura
 * 
 * Uso: node extract-chat-data.js
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
// EXTRAÇÃO DE DADOS DO CHAT
// =============================================================================

function extractChatData(captureData) {
  const chatData = {
    requests: [],
    responses: [],
    summary: {
      totalChatRequests: 0,
      totalChatResponses: 0,
      uniqueMessages: new Set(),
      messageTypes: new Set()
    }
  };

  log('🔍 Procurando requisições do endpoint /chat...', 'yellow');
  
  // Extrair requisições do chat
  captureData.requests.forEach(req => {
    try {
      if (req.url.includes('/chat') && req.method === 'POST') {
        chatData.summary.totalChatRequests++;
        
        const chatRequest = {
          timestamp: req.timestamp,
          url: req.url,
          method: req.method,
          headers: {
            authorization: req.headers?.authorization?.substring(0, 50) + '...',
            'content-type': req.headers?.['content-type'],
            'x-client-git-sha': req.headers?.['x-client-git-sha']
          }
        };

        // Parse payload
        if (req.postData) {
          try {
            const payload = JSON.parse(req.postData);
            chatRequest.payload = payload;
            
            // Extrair informações
            if (payload.message) {
              chatData.summary.uniqueMessages.add(payload.message);
            }
            if (payload.mode) {
              chatData.summary.messageTypes.add(payload.mode);
            }
          } catch (e) {
            chatRequest.payload = req.postData;
          }
        }

        chatData.requests.push(chatRequest);
      }
    } catch (e) {
      // Ignorar erros de parsing
    }
  });

  log(`✅ ${chatData.summary.totalChatRequests} requisições de chat encontradas`, 'green');
  log('');

  log('🔍 Procurando respostas do endpoint /chat...', 'yellow');

  // Extrair respostas do chat
  captureData.responses.forEach(res => {
    try {
      if (res.url.includes('/chat')) {
        chatData.summary.totalChatResponses++;
        
        const chatResponse = {
          timestamp: res.timestamp,
          url: res.url,
          status: res.status,
          headers: {
            'content-type': res.headers?.['content-type']
          }
        };

        // Parse body
        if (res.body && res.body !== '[Binary or unavailable]') {
          try {
            const body = JSON.parse(res.body);
            chatResponse.body = body;
            chatResponse.structure = getObjectStructure(body);
          } catch (e) {
            // Body muito grande ou não é JSON
            chatResponse.bodySize = res.body.length;
            chatResponse.note = 'Body too large or not JSON';
          }
        }

        chatData.responses.push(chatResponse);
      }
    } catch (e) {
      // Ignorar erros
    }
  });

  log(`✅ ${chatData.summary.totalChatResponses} respostas de chat encontradas`, 'green');
  log('');

  return chatData;
}

function getObjectStructure(obj, depth = 0, maxDepth = 4) {
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
// GERAÇÃO DE RELATÓRIO
// =============================================================================

function generateChatReport(chatData) {
  let report = '';
  
  report += '# 💬 LOVABLE CHAT API - ANÁLISE DETALHADA\n\n';
  report += `> Gerado em ${new Date().toLocaleString('pt-BR')}\n\n`;
  report += '---\n\n';

  // Estatísticas
  report += '## 📊 ESTATÍSTICAS\n\n';
  report += `- **Total de requisições de chat:** ${chatData.summary.totalChatRequests}\n`;
  report += `- **Total de respostas de chat:** ${chatData.summary.totalChatResponses}\n`;
  report += `- **Mensagens únicas:** ${chatData.summary.uniqueMessages.size}\n`;
  report += `- **Tipos de modo:** ${Array.from(chatData.summary.messageTypes).join(', ')}\n\n`;
  report += '---\n\n';

  // Mensagens enviadas
  if (chatData.summary.uniqueMessages.size > 0) {
    report += '## 💬 MENSAGENS ENVIADAS\n\n';
    Array.from(chatData.summary.uniqueMessages).forEach((msg, idx) => {
      report += `${idx + 1}. "${msg}"\n`;
    });
    report += '\n---\n\n';
  }

  // Estrutura de Request
  if (chatData.requests.length > 0) {
    report += '## 📤 ESTRUTURA DE REQUEST\n\n';
    report += '### Endpoint\n\n';
    report += '```\nPOST /projects/{uuid}/chat\n```\n\n';
    
    report += '### Headers\n\n';
    report += '```http\n';
    report += 'Authorization: Bearer {firebase_jwt_token}\n';
    report += 'Content-Type: application/json\n';
    report += 'x-client-git-sha: {git_sha}\n';
    report += '```\n\n';

    report += '### Payload Exemplo\n\n';
    report += '```json\n';
    report += JSON.stringify(chatData.requests[0].payload, null, 2);
    report += '\n```\n\n';
    report += '---\n\n';
  }

  // Estrutura de Response
  if (chatData.responses.length > 0) {
    report += '## 📥 ESTRUTURA DE RESPONSE\n\n';
    
    chatData.responses.forEach((res, idx) => {
      report += `### Response ${idx + 1}\n\n`;
      report += `- **Status:** ${res.status}\n`;
      report += `- **Timestamp:** ${res.timestamp}\n\n`;
      
      if (res.structure) {
        report += '**Estrutura:**\n```javascript\n';
        report += JSON.stringify(res.structure, null, 2);
        report += '\n```\n\n';
      }
      
      if (res.body && Object.keys(res.body).length < 20) {
        report += '**Body Completo:**\n```json\n';
        report += JSON.stringify(res.body, null, 2);
        report += '\n```\n\n';
      }
      
      if (res.note) {
        report += `*Nota: ${res.note}*\n\n`;
      }
    });
    
    report += '---\n\n';
  }

  // Implementação sugerida
  report += '## 🚀 IMPLEMENTAÇÃO NO CHATLOVE\n\n';
  report += '### 1. Estrutura de Mensagem\n\n';
  report += '```python\n';
  report += 'def create_chat_message(user_message: str, project_id: str):\n';
  report += '    return {\n';
  report += '        "message": user_message,\n';
  report += '        "id": f"umsg_{int(time.time() * 1000)}",\n';
  report += '        "mode": "instant",\n';
  report += '        "contains_error": False,\n';
  report += '        "chat_only": False,\n';
  report += '        "headless": False,\n';
  report += '        "debug_mode": False,\n';
  report += '        "noop_mode": False\n';
  report += '    }\n';
  report += '```\n\n';

  report += '### 2. Headers Necessários\n\n';
  report += '```python\n';
  report += 'headers = {\n';
  report += '    "Authorization": f"Bearer {firebase_token}",\n';
  report += '    "Content-Type": "application/json",\n';
  report += '    "x-client-git-sha": "cecc21f7a089150488df0c9ccc547e4489d871c7"\n';
  report += '}\n';
  report += '```\n\n';

  report += '### 3. Endpoint\n\n';
  report += '```python\n';
  report += 'url = f"https://api.lovable.dev/projects/{project_id}/chat"\n';
  report += 'response = requests.post(url, json=payload, headers=headers)\n';
  report += '```\n\n';

  report += '---\n\n';
  report += '*Análise gerada por Chat Data Extractor*\n';

  return report;
}

// =============================================================================
// MAIN
// =============================================================================

async function main() {
  log('═══════════════════════════════════════════════════════', 'cyan');
  log('💬 CHAT DATA EXTRACTOR', 'bright');
  log('═══════════════════════════════════════════════════════', 'cyan');
  log('');

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
  
  log(`📂 Processando: ${captureFile}`, 'blue');
  log('');

  // Carregar dados
  log('📖 Carregando arquivo...', 'yellow');
  const fileContent = fs.readFileSync(captureFile, 'utf8');
  
  log('🔍 Parsing JSON...', 'yellow');
  const data = JSON.parse(fileContent);
  log('');

  // Extrair dados do chat
  const chatData = extractChatData(data);

  // Gerar relatório
  log('📝 Gerando relatório...', 'blue');
  const report = generateChatReport(chatData);

  // Salvar arquivos
  const outputDir = path.join(capturesDir, 'chat-analysis');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 1. Relatório Markdown
  fs.writeFileSync(
    path.join(outputDir, 'chat-report.md'),
    report
  );
  log('✅ chat-report.md', 'green');

  // 2. Dados JSON
  const jsonData = {
    summary: {
      totalChatRequests: chatData.summary.totalChatRequests,
      totalChatResponses: chatData.summary.totalChatResponses,
      uniqueMessages: Array.from(chatData.summary.uniqueMessages),
      messageTypes: Array.from(chatData.summary.messageTypes)
    },
    requests: chatData.requests,
    responses: chatData.responses
  };

  fs.writeFileSync(
    path.join(outputDir, 'chat-data.json'),
    JSON.stringify(jsonData, null, 2)
  );
  log('✅ chat-data.json', 'green');

  log('');
  log('═══════════════════════════════════════════════════════', 'green');
  log('✅ EXTRAÇÃO COMPLETA!', 'bright');
  log('═══════════════════════════════════════════════════════', 'green');
  log('');
  log('📊 RESUMO:', 'yellow');
  log(`   - Requisições de chat: ${chatData.summary.totalChatRequests}`, 'cyan');
  log(`   - Respostas de chat: ${chatData.summary.totalChatResponses}`, 'cyan');
  log(`   - Mensagens únicas: ${chatData.summary.uniqueMessages.size}`, 'cyan');
  log('');
  log('📁 Arquivos gerados:', 'yellow');
  log(`   ${outputDir}/`, 'magenta');
  log('');
}

main();
