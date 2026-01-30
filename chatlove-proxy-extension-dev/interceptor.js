/**
 * ChatLove Interceptor - Captura requisições e respostas da Lovable
 * Usado para investigar o fluxo completo e resolver problema de "pendente"
 */

class LovableInterceptor {
  constructor() {
    this.requests = [];
    this.responses = [];
    this.lastChatTimestamp = 0;
    this.isRecording = false;
    
    this.setupInterceptor();
    this.setupMessageListener();
    
    console.log('[ChatLove Interceptor] Inicializado');
  }
  
  setupInterceptor() {
    // Interceptar fetch - APENAS para requisições não-ChatLove
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const [url, options] = args;
      const timestamp = Date.now();
      
      // Verificar se é requisição da extensão ChatLove
      const urlStr = url.toString();
      const isChatLoveRequest = urlStr.includes('chat.trafficai.cloud') || 
                               urlStr.includes('trafficai.cloud') ||
                               urlStr.includes('api/validate-license') ||
                               urlStr.includes('api/credits');
      
      // Se for requisição da extensão, executar sem interceptar
      if (isChatLoveRequest) {
        return await originalFetch(...args);
      }
      
      // Logar requisição se for da Lovable
      if (this.isLovableRequest(url)) {
        const requestData = {
          type: 'request',
          url: url.toString(),
          method: options?.method || 'GET',
          headers: options?.headers || {},
          body: options?.body,
          timestamp: timestamp,
          id: this.generateId()
        };
        
        this.requests.push(requestData);
        
        if (this.isRecording) {
          console.log('[Interceptor] 📤 Request:', {
            method: requestData.method,
            url: this.cleanUrl(requestData.url),
            body: this.cleanBody(requestData.body)
          });
        }
      }
      
      // Executar requisição original
      const response = await originalFetch(...args);
      
      // Logar resposta se for da Lovable
      if (this.isLovableRequest(url)) {
        const clonedResponse = response.clone();
        let responseBody = '';
        
        try {
          responseBody = await clonedResponse.text();
        } catch (e) {
          responseBody = '[Erro ao ler resposta]';
        }
        
        const responseData = {
          type: 'response',
          url: url.toString(),
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          body: responseBody,
          timestamp: Date.now(),
          requestId: this.findRequestId(url, timestamp)
        };
        
        this.responses.push(responseData);
        
        if (this.isRecording) {
          console.log('[Interceptor] 📥 Response:', {
            status: responseData.status,
            url: this.cleanUrl(responseData.url),
            bodyLength: responseBody.length,
            body: responseBody.substring(0, 200) + (responseBody.length > 200 ? '...' : '')
          });
        }
        
        // Se for resposta de chat, notificar extensão
        if (this.isChatResponse(url)) {
          this.notifyExtension('chat_response', responseData);
        }
      }
      
      return response;
    };
    
    // Interceptar XMLHttpRequest
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;
    
    XMLHttpRequest.prototype.open = function(method, url, ...args) {
      this._interceptorData = {
        method,
        url: url.toString(),
        timestamp: Date.now()
      };
      
      return originalXHROpen.call(this, method, url, ...args);
    };
    
    XMLHttpRequest.prototype.send = function(body) {
      if (this._interceptorData && window.lovableInterceptor.isLovableRequest(this._interceptorData.url)) {
        const requestData = {
          type: 'xhr_request',
          ...this._interceptorData,
          body: body,
          id: window.lovableInterceptor.generateId()
        };
        
        window.lovableInterceptor.requests.push(requestData);
        
        if (window.lovableInterceptor.isRecording) {
          console.log('[Interceptor] 📤 XHR Request:', {
            method: requestData.method,
            url: window.lovableInterceptor.cleanUrl(requestData.url)
          });
        }
        
        // Interceptar resposta
        this.addEventListener('readystatechange', function() {
          if (this.readyState === 4) {
            const responseData = {
              type: 'xhr_response',
              url: window.lovableInterceptor._interceptorData?.url,
              status: this.status,
              statusText: this.statusText,
              body: this.responseText,
              timestamp: Date.now(),
              requestId: requestData.id
            };
            
            window.lovableInterceptor.responses.push(responseData);
            
            if (window.lovableInterceptor.isRecording) {
              console.log('[Interceptor] 📥 XHR Response:', {
                status: responseData.status,
                url: window.lovableInterceptor.cleanUrl(responseData.url),
                bodyLength: this.responseText.length
              });
            }
          }
        });
      }
      
      return originalXHRSend.call(this, body);
    };
    
    // Interceptar EventSource (Server-Sent Events)
    const OriginalEventSource = window.EventSource;
    window.EventSource = function(url, config) {
      if (window.lovableInterceptor.isLovableRequest(url)) {
        console.log('[Interceptor] 🔄 SSE Conectando:', window.lovableInterceptor.cleanUrl(url));
        
        window.lovableInterceptor.requests.push({
          type: 'sse_connect',
          url: url.toString(),
          timestamp: Date.now(),
          id: window.lovableInterceptor.generateId()
        });
      }
      
      const es = new OriginalEventSource(url, config);
      
      if (window.lovableInterceptor.isLovableRequest(url)) {
        // Interceptar mensagens
        es.addEventListener('message', (event) => {
          const messageData = {
            type: 'sse_message',
            url: url.toString(),
            data: event.data,
            timestamp: Date.now()
          };
          
          window.lovableInterceptor.responses.push(messageData);
          
          if (window.lovableInterceptor.isRecording) {
            console.log('[Interceptor] 📨 SSE Message:', {
              url: window.lovableInterceptor.cleanUrl(url),
              data: event.data.substring(0, 100) + (event.data.length > 100 ? '...' : '')
            });
          }
          
          // Notificar extensão sobre streaming
          window.lovableInterceptor.notifyExtension('sse_message', messageData);
        });
        
        // Interceptar outros eventos
        ['open', 'error', 'close'].forEach(eventType => {
          es.addEventListener(eventType, (event) => {
            if (window.lovableInterceptor.isRecording) {
              console.log(`[Interceptor] 🔄 SSE ${eventType.toUpperCase()}:`, window.lovableInterceptor.cleanUrl(url));
            }
          });
        });
      }
      
      return es;
    };
  }
  
  setupMessageListener() {
    // Escutar mensagens da extensão
    window.addEventListener('message', (event) => {
      if (event.data.type === 'CHATLOVE_START_RECORDING') {
        this.startRecording();
      } else if (event.data.type === 'CHATLOVE_STOP_RECORDING') {
        this.stopRecording();
      } else if (event.data.type === 'CHATLOVE_GET_REQUESTS') {
        this.sendRequestsToExtension();
      }
    });
  }
  
  isLovableRequest(url) {
    const urlStr = url.toString();
    return urlStr.includes('lovable.dev') || 
           urlStr.includes('api.lovable') ||
           urlStr.includes('lovable.com');
  }
  
  isChatResponse(url) {
    const urlStr = url.toString();
    return urlStr.includes('/chat') || 
           urlStr.includes('/message') ||
           urlStr.includes('/stream');
  }
  
  cleanUrl(url) {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname + (urlObj.search ? '?' + urlObj.search.substring(0, 50) : '');
    } catch (e) {
      return url.substring(0, 100);
    }
  }
  
  cleanBody(body) {
    if (!body) return null;
    
    if (typeof body === 'string') {
      try {
        const parsed = JSON.parse(body);
        return {
          ...parsed,
          message: parsed.message ? parsed.message.substring(0, 100) + '...' : parsed.message
        };
      } catch (e) {
        return body.substring(0, 100) + '...';
      }
    }
    
    return '[Body não string]';
  }
  
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
  
  findRequestId(url, timestamp) {
    // Encontrar requisição correspondente (dentro de 1 segundo)
    const request = this.requests.find(r => 
      r.url === url && Math.abs(r.timestamp - timestamp) < 1000
    );
    return request ? request.id : null;
  }
  
  startRecording() {
    this.isRecording = true;
    this.lastChatTimestamp = Date.now();
    this.requests = [];
    this.responses = [];
    
    console.log('[Interceptor] 🔴 Gravação iniciada');
  }
  
  stopRecording() {
    this.isRecording = false;
    console.log('[Interceptor] ⏹️ Gravação parada');
    console.log(`[Interceptor] Capturadas ${this.requests.length} requisições e ${this.responses.length} respostas`);
  }
  
  getRequestsAfterChat() {
    return {
      requests: this.requests.filter(r => r.timestamp > this.lastChatTimestamp),
      responses: this.responses.filter(r => r.timestamp > this.lastChatTimestamp)
    };
  }
  
  notifyExtension(type, data) {
    // Enviar dados para a extensão via postMessage
    window.postMessage({
      type: 'LOVABLE_INTERCEPTED',
      subType: type,
      data: data
    }, '*');
  }
  
  sendRequestsToExtension() {
    const data = this.getRequestsAfterChat();
    this.notifyExtension('requests_dump', data);
  }
  
  // Métodos públicos para debug
  exportData() {
    return {
      requests: this.requests,
      responses: this.responses,
      timestamp: Date.now()
    };
  }
  
  clearData() {
    this.requests = [];
    this.responses = [];
    console.log('[Interceptor] 🗑️ Dados limpos');
  }
}

// Inicializar interceptor globalmente
window.lovableInterceptor = new LovableInterceptor();

// Expor métodos para debug no console
window.debugInterceptor = {
  start: () => window.lovableInterceptor.startRecording(),
  stop: () => window.lovableInterceptor.stopRecording(),
  export: () => window.lovableInterceptor.exportData(),
  clear: () => window.lovableInterceptor.clearData(),
  requests: () => window.lovableInterceptor.getRequestsAfterChat()
};

console.log('[ChatLove] Interceptor carregado. Use window.debugInterceptor para debug.');