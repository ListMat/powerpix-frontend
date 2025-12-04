# 🏦 Integração Asaas - PowerPix

## 📋 Visão Geral

Integração completa com o gateway de pagamentos Asaas para processar depósitos via Pix.

## 🔧 Configuração

### 1. Criar Conta no Asaas

1. Acesse [Asaas.com](https://www.asaas.com/)
2. Crie sua conta
3. Acesse o ambiente de **Sandbox** (testes) ou **Produção**

### 2. Obter API Key

1. No painel do Asaas, vá em **Configurações** → **Integrações** → **API Key**
2. Gere uma nova chave
3. Copie a API Key

**Importante:**
- **Sandbox**: Use para testes (não processa pagamentos reais)
- **Produção**: Use apenas quando estiver pronto para produção

### 3. Configurar .env

Adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# Asaas Configuration
ASAAS_API_KEY=sua_api_key_aqui
ASAAS_API_URL=https://api.asaas.com/v3
ASAAS_WEBHOOK_TOKEN=token_secreto_opcional
```

**URLs:**
- Sandbox: `https://sandbox.asaas.com/api/v3`
- Produção: `https://api.asaas.com/v3`

### 4. Configurar Webhook no Asaas

1. No painel do Asaas: **Configurações** → **Integrações** → **Webhooks**
2. Adicione uma nova URL de webhook:
   ```
   https://seu-dominio.com/finance/webhook/asaas
   ```
3. Selecione os eventos:
   - ✅ `PAYMENT_RECEIVED` - Pagamento recebido
   - ✅ `PAYMENT_CONFIRMED` - Pagamento confirmado
   - ✅ `PAYMENT_OVERDUE` - Pagamento vencido
   - ✅ `PAYMENT_REFUNDED` - Pagamento estornado

4. (Opcional) Configure um token de autenticação personalizado

---

## 🚀 Como Funciona

### Fluxo de Depósito

```
1. Usuário solicita depósito → POST /finance/deposit
2. Sistema busca/cria cliente no Asaas
3. Sistema cria cobrança Pix no Asaas
4. Asaas gera QR Code Pix
5. Sistema retorna QR Code para usuário
6. Usuário paga o Pix no banco
7. Asaas detecta pagamento → Envia webhook
8. Sistema recebe webhook → POST /finance/webhook/asaas
9. Sistema valida e credita saldo do usuário
10. Usuário recebe notificação de saldo creditado
```

---

## 📡 Endpoints da API

### POST /finance/deposit

Cria uma cobrança Pix via Asaas.

**Request:**
```json
{
  "telegram_id": 123456789,
  "valor": 50.00
}
```

**Response:**
```json
{
  "transaction_id": 1,
  "pix_code": "00020126580014br.gov.bcb.pix...",
  "qr_code_base64": "data:image/png;base64,iVBORw0KGgo...",
  "valor": 50.0,
  "status": "PENDENTE",
  "payment_id": "pay_abc123xyz",
  "expires_at": "2025-12-05",
  "created_at": "2025-12-04T12:00:00"
}
```

**Campos:**
- `transaction_id`: ID da transação local
- `pix_code`: Código Pix copia e cola
- `qr_code_base64`: Imagem do QR Code em base64
- `payment_id`: ID da cobrança no Asaas
- `expires_at`: Data de vencimento

---

### POST /finance/webhook/asaas

Webhook para receber notificações do Asaas.

**Headers:**
- `asaas-access-token`: Token de autenticação (opcional)

**Eventos processados:**

#### PAYMENT_RECEIVED / PAYMENT_CONFIRMED
Pagamento recebido ou confirmado → **Credita saldo**

```json
{
  "event": "PAYMENT_RECEIVED",
  "payment": {
    "id": "pay_abc123xyz",
    "customer": "cus_xyz789",
    "value": 50.00,
    "status": "RECEIVED",
    "billingType": "PIX",
    "confirmedDate": "2025-12-04 12:05:00"
  }
}
```

#### PAYMENT_OVERDUE
Pagamento vencido → **Marca como FALHA**

#### PAYMENT_REFUNDED
Pagamento estornado → **Marca como CANCELADO**

---

## 🔒 Segurança

### 1. Validação de Token (Opcional)
Configure um token secreto no `.env`:
```env
ASAAS_WEBHOOK_TOKEN=seu_token_super_secreto_123
```

E no código do webhook (descomente se quiser usar):
```python
if asaas_access_token != settings.ASAAS_WEBHOOK_TOKEN:
    raise HTTPException(status_code=403, detail="Token inválido")
```

### 2. Prevenção de Duplicação
O sistema verifica se a transação já foi processada antes de creditar:
```python
if transacao.status == StatusTransacao.PAGO:
    return {"status": "already_processed"}
```

### 3. Transações Atômicas
Saldo é creditado em uma única transação do banco de dados.

### 4. Logs Detalhados
Todos os eventos são logados para auditoria.

---

## 🧪 Testando com Sandbox

### 1. Configurar Sandbox
```env
ASAAS_API_KEY=sua_chave_sandbox
ASAAS_API_URL=https://sandbox.asaas.com/api/v3
```

### 2. Criar Depósito
```bash
curl -X POST http://localhost:8000/finance/deposit \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "valor": 50.00
  }'
```

### 3. Simular Pagamento no Painel do Asaas

1. Acesse o painel Sandbox do Asaas
2. Vá em **Cobranças**
3. Localize a cobrança criada
4. Clique em **Simular Pagamento**
5. O webhook será enviado automaticamente

### 4. Verificar Saldo
```bash
curl http://localhost:8000/finance/balance/123456789
```

Deve mostrar o saldo creditado!

---

## 💳 Testando Pix Real (Sandbox)

O Asaas Sandbox permite testar com **Pix de verdade** (mas os valores são fictícios):

1. Use a API Key do **Sandbox**
2. Gere um QR Code Pix
3. Escaneie com seu app bancário
4. O valor será **R$ 0,01** (sandbox)
5. O webhook será enviado quando "pagar"

---

## 📊 Mapeamento de Status

### Status Asaas → Status Interno

| Status Asaas | Status Interno | Descrição |
|-------------|----------------|-----------|
| `PENDING` | `PENDENTE` | Aguardando pagamento |
| `RECEIVED` | `PAGO` | Pagamento recebido |
| `CONFIRMED` | `PAGO` | Pagamento confirmado |
| `OVERDUE` | `FALHA` | Vencido |
| `REFUNDED` | `CANCELADO` | Estornado |
| `AWAITING_RISK_ANALYSIS` | `PENDENTE` | Em análise |

---

## 🐛 Troubleshooting

### Webhook não está sendo recebido

**Possíveis causas:**
1. URL do webhook incorreta no painel Asaas
2. Servidor não está acessível publicamente
3. Firewall bloqueando requisições do Asaas

**Solução:**
- Use ngrok para expor localhost
- Verifique logs do servidor
- Teste manualmente com curl

### Erro: "Cliente não encontrado"

**Causa:** Cliente não foi criado no Asaas

**Solução:** O sistema cria automaticamente, mas você pode verificar manualmente:
```bash
curl https://sandbox.asaas.com/api/v3/customers \
  -H "access_token: SUA_API_KEY" \
  -d "externalReference=123456789"
```

### QR Code não aparece

**Causa:** Cobrança Pix não foi gerada corretamente

**Solução:** Verifique se:
- API Key está correta
- Conta Asaas está ativa
- Pix está habilitado na conta

### Saldo não foi creditado

**Causa:** Webhook não foi processado

**Solução:**
1. Verifique logs do servidor
2. Confira se o evento foi `PAYMENT_RECEIVED` ou `PAYMENT_CONFIRMED`
3. Teste manualmente enviando o webhook:

```bash
curl -X POST http://localhost:8000/finance/webhook/asaas \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_RECEIVED",
    "payment": {
      "id": "pay_abc123xyz",
      "value": 50.00,
      "status": "RECEIVED"
    }
  }'
```

---

## 📈 Monitoramento

### Logs Importantes

```
✓ Cliente criado no Asaas: cus_xyz789
✓ Cobrança Pix criada no Asaas: pay_abc123
✓ QR Code Pix obtido para cobrança: pay_abc123
✓ Depósito Asaas confirmado: Transaction ID 1 - Payment ID pay_abc123 - Valor R$ 50.00
```

### Consultar Status de Cobrança

Via API Asaas:
```bash
curl https://api.asaas.com/v3/payments/pay_abc123 \
  -H "access_token: SUA_API_KEY"
```

Via sistema (endpoint interno):
```bash
curl http://localhost:8000/finance/transactions/123456789
```

---

## 🚀 Deploy em Produção

### Checklist:

- [ ] Trocar API Key para **Produção**
- [ ] Atualizar `ASAAS_API_URL` para produção
- [ ] Configurar webhook com URL pública HTTPS
- [ ] Habilitar validação de token no webhook
- [ ] Configurar certificado SSL válido
- [ ] Testar fluxo completo com valor pequeno
- [ ] Ativar monitoramento e alertas
- [ ] Revisar taxas e limites com Asaas

### Taxas Asaas (Pix)

- **Pix**: R$ 0,40 a R$ 3,59 por transação (depende do plano)
- **Prazo de recebimento**: D+0 (mesmo dia)

---

## 📞 Suporte

- **Documentação Asaas**: https://docs.asaas.com/
- **Suporte Asaas**: suporte@asaas.com
- **Status da API**: https://status.asaas.com/

---

## ✅ Vantagens do Asaas

1. ✅ **Fácil integração** - API REST bem documentada
2. ✅ **Pix instantâneo** - Recebe no mesmo dia (D+0)
3. ✅ **Sandbox completo** - Teste tudo antes de produção
4. ✅ **QR Code automático** - Gerado pela API
5. ✅ **Webhooks confiáveis** - Notificações em tempo real
6. ✅ **Dashboard completo** - Gerencie tudo pelo painel
7. ✅ **Sem mensalidade** - Paga só por transação
8. ✅ **Suporte nacional** - Atendimento em português

---

## 🎯 Próximos Passos

- [ ] Implementar sistema de saque
- [ ] Adicionar notificações no Telegram quando saldo for creditado
- [ ] Criar dashboard de transações no admin
- [ ] Implementar relatórios financeiros
- [ ] Adicionar suporte a boleto bancário
- [ ] Integrar com sistema de comissões/afiliados

