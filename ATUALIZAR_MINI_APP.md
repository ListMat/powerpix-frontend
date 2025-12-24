# 📱 Como Atualizar o Link do Mini App no Telegram

## 🔗 URL Atual do Mini App

A URL do seu Mini App é construída automaticamente a partir do `WEBHOOK_URL` configurado no `.env`:

```
{WEBHOOK_URL}/webapp
```

**URL Completa:** `https://peacelike-commiseratively-sandy.ngrok-free.dev/webapp`

## 📋 Passo a Passo para Atualizar no BotFather

### 1. Abra o BotFather no Telegram
- Procure por `@BotFather` no Telegram
- Ou acesse: https://t.me/BotFather

### 2. Inicie o processo de atualização
Envie o comando:
```
/newapp
```

### 3. Selecione seu bot
- O BotFather mostrará uma lista dos seus bots
- Selecione o bot do PowerPix

### 4. Configure o Mini App
O BotFather vai perguntar:
- **Title** (Título): `PowerPix` (ou o nome que você preferir)
- **Short name** (Nome curto): `powerpix` (ou o nome curto que você preferir)
- **Description** (Descrição): `Sistema de Loteria PowerPix`
- **Photo** (Foto): Opcional - você pode enviar uma imagem ou pular
- **Web App URL** (URL do Mini App): **Cole a URL completa abaixo**

### 5. Cole a URL do Mini App
```
https://peacelike-commiseratively-sandy.ngrok-free.dev/webapp
```

### 6. Confirme
O BotFather confirmará que o Mini App foi atualizado com sucesso.

## ⚠️ Importante

1. **URL deve ser HTTPS**: Certifique-se de que a URL começa com `https://`
2. **URL deve estar acessível**: O servidor deve estar rodando e acessível publicamente
3. **ngrok deve estar ativo**: Se estiver usando ngrok, certifique-se de que está rodando
4. **URL pode mudar**: Se você mudar o `WEBHOOK_URL` no `.env`, precisará atualizar o Mini App novamente

## 🔄 Se a URL do ngrok mudar

Se você reiniciar o ngrok e receber uma nova URL:

1. Atualize o `WEBHOOK_URL` no arquivo `.env`
2. Reinicie o servidor
3. Execute `python setup_webhook.py` para reconfigurar o webhook
4. Atualize o Mini App no BotFather com a nova URL seguindo os passos acima

## ✅ Verificar se está funcionando

1. Envie `/start` para o bot
2. Clique no botão do Mini App
3. O Mini App deve abrir com a interface do PowerPix

## 🐛 Problemas Comuns

### Mini App não abre
- Verifique se a URL está correta e acessível
- Certifique-se de que o servidor está rodando
- Verifique se o ngrok está ativo (se estiver usando)

### Erro 404
- Verifique se a rota `/webapp` está configurada corretamente
- Certifique-se de que o servidor está rodando na porta correta

### Mini App abre mas não carrega
- Verifique os logs do servidor para erros
- Verifique se o arquivo `index.html` está sendo servido corretamente
- Verifique o console do navegador (F12) para erros JavaScript

