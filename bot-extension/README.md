# Lovable Chat Extension

Popup de chat que usa as funcoes Supabase `radioai-authorization` e `radioai-proxy` para falar com o projeto Lovable.

## Fluxo rapido
- Campo de identificador numerico no topo. Clique em **Autorizar** para salvar no storage local e buscar o token via POST `https://idpwseayxycpgtmhxgsu.supabase.co/functions/v1/radioai-authorization` com body `{ "identificador": "<id>" }`.
- O token (e a validade retornada) ficam salvos; o status aparece abaixo do campo.
- O `projectId` e lido da URL ativa `lovable.dev/projects/<id>` ou do valor salvo manualmente.
- Envio de mensagens usa POST `https://idpwseayxycpgtmhxgsu.supabase.co/functions/v1/radioai-proxy` com header `Authorization: Bearer <token>` e body:
```json
{
  "idpage": "<projectId>",
  "token": "<token>",
  "requestBody": { "message": "<texto>" }
}
```
- Historico do chat e contagem de tokens economizados permanecem no `chrome.storage.local`. Upload segue opcional (UI comentada no HTML).

## Instalar no Chrome (modo dev)
1. Abra `chrome://extensions` e ative **Modo desenvolvedor**.
2. Clique em **Carregar sem empacotar** e selecione a pasta `bot-extension`.
3. Abra o popup no icone da extensao para testar.

## Uso
1. Preencha o identificador numerico e clique em **Autorizar** (token fica salvo com validade).
2. Digite a mensagem e clique **Enviar** (Enter envia, Shift+Enter quebra linha).
3. Use **Reiniciar** para limpar historico e contador de tokens.
4. Se o token expirar, clique em **Autorizar** novamente.

## APIs usadas
- Autorizacao: POST `https://idpwseayxycpgtmhxgsu.supabase.co/functions/v1/radioai-authorization` (body `{"identificador":"<id>"}`)
- Proxy: POST `https://idpwseayxycpgtmhxgsu.supabase.co/functions/v1/radioai-proxy`
  - Header: `Authorization: Bearer <token>`
  - Body: `{"idpage":"<projectId>","token":"<token>","requestBody":{"message":"<texto>"}}`

## Obfuscar popup.js antes de publicar
1. Instale o obfuscador: `npm install --global javascript-obfuscator` (ou use `npx javascript-obfuscator` sem instalar globalmente).
2. Gere um JS ofuscado: `javascript-obfuscator popup.js --output popup.obf.js --compact true --controlFlowFlattening true --selfDefending true`.
3. Substitua `popup.js` pelo `popup.obf.js` na build que sera publicada (guarde o original para manutencao).
4. Teste o popup apos a troca para garantir que a logica continua funcionando.

## Estrutura rapida
```
manifest.json
popup.html
popup.js
icons/logo.png
```
