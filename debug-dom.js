/**
 * Script de Debug para Investigar DOM do Lovable
 * 
 * COMO USAR:
 * 1. Abrir projeto no Lovable.dev
 * 2. Pressionar F12 (DevTools)
 * 3. Ir para aba Console
 * 4. Copiar e colar este script completo
 * 5. Pressionar Enter
 * 6. Copiar os resultados e enviar
 */

console.log('🔍 ===== INVESTIGAÇÃO DOM LOVABLE =====');
console.log('');

// 1. TEXTAREAS
console.log('📝 TEXTAREAS:');
const textareas = document.querySelectorAll('textarea');
console.log(`Total: ${textareas.length}`);
textareas.forEach((ta, i) => {
  console.log(`  [${i}] Placeholder: "${ta.placeholder}"`);
  console.log(`      ID: "${ta.id}"`);
  console.log(`      Class: "${ta.className}"`);
  console.log(`      Parent: ${ta.parentElement?.tagName}.${ta.parentElement?.className}`);
});
console.log('');

// 2. CONTENTEDITABLE
console.log('✏️ CONTENTEDITABLE:');
const editables = document.querySelectorAll('[contenteditable="true"]');
console.log(`Total: ${editables.length}`);
editables.forEach((el, i) => {
  console.log(`  [${i}] Tag: ${el.tagName}`);
  console.log(`      ID: "${el.id}"`);
  console.log(`      Class: "${el.className}"`);
  console.log(`      Text: "${el.textContent.substring(0, 50)}..."`);
});
console.log('');

// 3. INPUTS TEXT
console.log('📥 INPUTS TEXT:');
const inputs = document.querySelectorAll('input[type="text"]');
console.log(`Total: ${inputs.length}`);
inputs.forEach((inp, i) => {
  console.log(`  [${i}] Placeholder: "${inp.placeholder}"`);
  console.log(`      ID: "${inp.id}"`);
  console.log(`      Class: "${inp.className}"`);
});
console.log('');

// 4. ROLE TEXTBOX
console.log('📋 ROLE TEXTBOX:');
const textboxes = document.querySelectorAll('[role="textbox"]');
console.log(`Total: ${textboxes.length}`);
textboxes.forEach((tb, i) => {
  console.log(`  [${i}] Tag: ${tb.tagName}`);
  console.log(`      ID: "${tb.id}"`);
  console.log(`      Class: "${tb.className}"`);
});
console.log('');

// 5. IFRAMES
console.log('🖼️ IFRAMES:');
const iframes = document.querySelectorAll('iframe');
console.log(`Total: ${iframes.length}`);
iframes.forEach((iframe, i) => {
  console.log(`  [${i}] SRC: ${iframe.src}`);
  console.log(`      ID: "${iframe.id}"`);
  console.log(`      Class: "${iframe.className}"`);
  
  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    const iframeTextareas = iframeDoc.querySelectorAll('textarea');
    const iframeEditables = iframeDoc.querySelectorAll('[contenteditable="true"]');
    
    console.log(`      ✅ Acessível! Textareas: ${iframeTextareas.length}, Editables: ${iframeEditables.length}`);
    
    if (iframeTextareas.length > 0) {
      iframeTextareas.forEach((ta, j) => {
        console.log(`         Textarea [${j}]: "${ta.placeholder}"`);
      });
    }
    
    if (iframeEditables.length > 0) {
      iframeEditables.forEach((ed, j) => {
        console.log(`         Editable [${j}]: ${ed.tagName}.${ed.className}`);
      });
    }
  } catch (e) {
    console.log(`      ❌ CORS Blocked: ${e.message}`);
  }
});
console.log('');

// 6. BOTÕES (possíveis botões de envio)
console.log('🔘 BOTÕES DE ENVIO:');
const buttons = document.querySelectorAll('button');
console.log(`Total de botões: ${buttons.length}`);
const sendButtons = Array.from(buttons).filter(btn => {
  const text = btn.textContent.toLowerCase();
  const aria = btn.getAttribute('aria-label')?.toLowerCase() || '';
  const type = btn.type;
  const hasSvg = btn.querySelector('svg') !== null;
  
  return type === 'submit' || 
         text.includes('send') || 
         text.includes('enviar') ||
         aria.includes('send') ||
         aria.includes('submit') ||
         (hasSvg && text === '');
});

console.log(`Possíveis botões de envio: ${sendButtons.length}`);
sendButtons.forEach((btn, i) => {
  console.log(`  [${i}] Text: "${btn.textContent.trim()}"`);
  console.log(`      Type: ${btn.type}`);
  console.log(`      Aria: "${btn.getAttribute('aria-label')}"`);
  console.log(`      Class: "${btn.className}"`);
  console.log(`      Has SVG: ${btn.querySelector('svg') !== null}`);
});
console.log('');

// 7. SHADOW DOM
console.log('🌑 SHADOW DOM:');
const elementsWithShadow = document.querySelectorAll('*');
let shadowCount = 0;
elementsWithShadow.forEach(el => {
  if (el.shadowRoot) {
    shadowCount++;
    console.log(`  Shadow Root em: ${el.tagName}.${el.className}`);
    const shadowTextareas = el.shadowRoot.querySelectorAll('textarea');
    const shadowEditables = el.shadowRoot.querySelectorAll('[contenteditable="true"]');
    console.log(`    Textareas: ${shadowTextareas.length}, Editables: ${shadowEditables.length}`);
  }
});
console.log(`Total de Shadow Roots: ${shadowCount}`);
console.log('');

// 8. RESUMO
console.log('📊 ===== RESUMO =====');
console.log(`Textareas: ${textareas.length}`);
console.log(`Contenteditable: ${editables.length}`);
console.log(`Inputs text: ${inputs.length}`);
console.log(`Role textbox: ${textboxes.length}`);
console.log(`Iframes: ${iframes.length}`);
console.log(`Botões de envio: ${sendButtons.length}`);
console.log(`Shadow Roots: ${shadowCount}`);
console.log('');
console.log('✅ Investigação completa! Copie todos os resultados acima.');
