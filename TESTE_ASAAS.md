# 🧪 Teste Rápido - Integração Asaas

## ✅ Chave API Configurada

Sua chave de **PRODUÇÃO** foi configurada:
```
$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjM1ZGI1YmRmLTYyMjAtNGUxZS05MTZhLTBjYzYyMmE4ZTFhNDo6JGFhY2hfOTJjMjRmMTYtNzg0Zi00NGM1LTg3OWYtMzNkMTg2N2UxNjg2
```

⚠️ **IMPORTANTE**: Esta é uma chave de **PRODUÇÃO**! Transações serão reais.

---

## 🚀 Como Testar

### 1. Iniciar o Servidor

```bash
.venv\Scripts\python.exe app.py
```

Ou:
```bash
.venv\Scripts\activate
python app.py
```

### 2. Configurar Webhook no Asaas

1. Acesse: https://www.asaas.com/
2. Faça login
3. Vá em: **Configurações** → **Integrações** → **Webhooks**
4. Adicione uma nova URL:
   ```
   https://peacelike-commiseratively-sandy.ngrok-free.dev/finance/webhook/asaas
   ```
5. Selecione os eventos:
   - ✅ PAYMENT_RECEIVED
   - ✅ PAYMENT_CONFIRMED
   - ✅ PAYMENT_OVERDUE
   - ✅ PAYMENT_REFUNDED

### 3. Testar Criação de Depósito

**Request:**
```bash
curl -X POST http://localhost:8000/finance/deposit \
  -H "Content-Type: application/json" \
  -d "{\"telegram_id\": 123456789, \"valor\": 10.00}"
```

**Response esperado:**
```json
{
  "transaction_id": 1,
  "pix_code": "00020126580014br.gov.bcb.pix...",
  "qr_code_base64": "data:image/png;base64,iVBORw0KGgo...",
  "valor": 10.0,
  "status": "PENDENTE",
  "payment_id": "pay_abc123xyz",
  "expires_at": "2025-12-05",
  "created_at": "2025-12-04T..."
}
```

### 4. Pagar o Pix

**Opção A - Via QR Code:**
1. Copie o `qr_code_base64` da response
2. Cole em um visualizador de imagem base64 ou salve como PNG
3. Escaneie com seu app bancário
4. Pague **R$ 10,00** (valor real!)

**Opção B - Via Copia e Cola:**
1. Copie o `pix_code` da response
2. Abra seu app bancário
3. Escolha "Pix Copia e Cola"
4. Cole o código
5. Pague **R$ 10,00**

### 5. Verificar Webhook

Após pagar, o Asaas enviará um webhook para:
```
POST /finance/webhook/asaas
```

**Logs esperados no servidor:**
```
INFO - Webhook Asaas recebido: PAYMENT_RECEIVED
INFO - ✓ Depósito Asaas confirmado: Transaction ID 1 - Payment ID pay_abc123 - Valor R$ 10.00
```

### 6. Verificar Saldo

```bash
curl http://localhost:8000/finance/balance/123456789
```

**Response esperado:**
```json
{
  "telegram_id": 123456789,
  "nome": "User_123456789",
  "saldo": 10.0
}
```

---

## 🎯 Teste Completo no Telegram

### 1. Iniciar bot
```
/start
```

### 2. Ver saldo
```
/saldo
```

Deve mostrar: **R$ 10,00**

### 3. Fazer aposta

1. Clique em "🎲 Fazer Aposta"
2. Selecione 20 números brancos e 5 vermelhos
3. Confirme

**Resultado esperado:**
```
✅ Aposta registrada com sucesso!

📊 Você selecionou 25 números:
⚪ Brancos: 20
🔴 Powerballs: 5

💰 Valor: R$ 5.00
💵 Saldo restante: R$ 5.00

🎯 Boa sorte no sorteio!
```

---

## 🐛 Troubleshooting

### Erro: "Erro ao criar cliente: Unauthorized"

**Causa:** Chave API inválida ou incorreta

**Solução:**
1. Verifique se copiou a chave completa
2. Confirme que está usando a chave de PRODUÇÃO
3. Teste manualmente:

```bash
curl https://api.asaas.com/v3/customers \
  -H "access_token: $aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjM1ZGI1YmRmLTYyMjAtNGUxZS05MTZhLTBjYzYyMmE4ZTFhNDo6JGFhY2hfOTJjMjRmMTYtNzg0Zi00NGM1LTg3OWYtMzNkMTg2N2UxNjg2" \
  -d "name=Teste"
```

### Webhook não recebe eventos

**Causa:** URL não está acessível ou não configurada no Asaas

**Solução:**
1. Confirme que o ngrok está rodando
2. Verifique a URL no painel do Asaas
3. Teste manualmente:

```bash
curl -X POST http://localhost:8000/finance/webhook/asaas \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_RECEIVED",
    "payment": {
      "id": "pay_teste123",
      "value": 10.00,
      "status": "RECEIVED"
    }
  }'
```

### QR Code não aparece

**Causa:** Pix pode não estar habilitado na conta Asaas

**Solução:**
1. Acesse o painel do Asaas
2. Vá em **Configurações** → **Formas de Pagamento**
3. Habilite o **Pix**
4. Complete o cadastro se necessário

---

## 💰 Valores de Teste

Como você está usando a API de **PRODUÇÃO**, recomendo testar com valores pequenos:

- ✅ **R$ 1,00** - Teste mínimo
- ✅ **R$ 5,00** - Valor de uma aposta
- ✅ **R$ 10,00** - Duas apostas
- ✅ **R$ 25,00** - Valor de um pacote

⚠️ **Atenção**: Todos os valores são REAIS!

---

## 📊 Monitorar no Painel Asaas

1. Acesse: https://www.asaas.com/
2. Vá em **Cobranças**
3. Veja todas as cobranças Pix criadas
4. Status:
   - 🟡 Pendente
   - 🟢 Recebido
   - 🔵 Confirmado
   - 🔴 Vencido

---

## ✅ Checklist de Teste

- [ ] Servidor iniciado
- [ ] Webhook configurado no Asaas
- [ ] Depósito criado via API
- [ ] QR Code gerado
- [ ] Pix pago com sucesso
- [ ] Webhook recebido
- [ ] Saldo creditado
- [ ] Aposta feita no bot
- [ ] Saldo deduzido corretamente

---

## 📞 Suporte Asaas

Se tiver problemas:
- **Email**: suporte@asaas.com
- **Telefone**: (31) 3271-8008
- **WhatsApp**: (31) 97196-0008
- **Documentação**: https://docs.asaas.com/

---

## 🎉 Sucesso!

Se tudo funcionou:
- ✅ Integração Asaas está funcionando
- ✅ Pix está sendo processado
- ✅ Webhooks estão sendo recebidos
- ✅ Saldo está sendo creditado
- ✅ Apostas estão deduzindo saldo

**Próximo passo:** Testar com usuários reais no Telegram!

