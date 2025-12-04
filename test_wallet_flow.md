# 🧪 Guia de Testes - Sistema de Wallet

## Pré-requisitos
- Servidor rodando em `http://localhost:8000`
- Bot Telegram configurado
- Cliente HTTP (curl, Postman, ou Insomnia)

## 1️⃣ Testar Criação de Depósito

### Request:
```bash
curl -X POST http://localhost:8000/finance/deposit \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "valor": 50.00
  }'
```

### Response esperado:
```json
{
  "transaction_id": 1,
  "pix_code": "00020126580014br.gov.bcb.pix0136PIX_ABC123...",
  "valor": 50.0,
  "status": "PENDENTE",
  "created_at": "2025-12-04T12:00:00.000000"
}
```

✅ **Validações:**
- Transaction ID foi criado
- Status é PENDENTE
- Gateway ID foi gerado
- Código Pix foi retornado

---

## 2️⃣ Simular Pagamento do Pix

Copie o `gateway_id` da response anterior (ex: PIX_ABC123).

### Request:
```bash
curl -X POST http://localhost:8000/finance/test/simulate-payment/PIX_ABC123
```

### Response esperado:
```json
{
  "status": "success",
  "transaction_id": 1,
  "novo_saldo": 50.0,
  "message": "Depósito creditado com sucesso"
}
```

✅ **Validações:**
- Status mudou para PAGO
- Saldo foi creditado
- Se tentar novamente, deve retornar "already_processed"

---

## 3️⃣ Verificar Saldo

### Request:
```bash
curl http://localhost:8000/finance/balance/123456789
```

### Response esperado:
```json
{
  "telegram_id": 123456789,
  "nome": "User_123456789",
  "saldo": 50.0
}
```

✅ **Validações:**
- Saldo reflete o depósito anterior
- Usuário foi criado automaticamente

---

## 4️⃣ Verificar Histórico de Transações

### Request:
```bash
curl http://localhost:8000/finance/transactions/123456789?limit=10
```

### Response esperado:
```json
{
  "telegram_id": 123456789,
  "transactions": [
    {
      "id": 1,
      "tipo": "DEPOSITO",
      "valor": 50.0,
      "status": "PAGO",
      "descricao": "Depósito via Pix - R$ 50.00",
      "created_at": "2025-12-04T12:00:00.000000",
      "updated_at": "2025-12-04T12:05:00.000000"
    }
  ]
}
```

---

## 5️⃣ Criar um Sorteio (Admin)

Antes de fazer apostas, você precisa de um sorteio ABERTO.

### Via SQLite:
```sql
INSERT INTO sorteios (status, premio_base, revenue, meta_arrecadacao, taxa_inicial, taxa_pos_meta)
VALUES ('ABERTO', 1000.0, 0.0, 3000.0, 0.3, 0.9);
```

### Ou via API Admin (se tiver endpoint):
```bash
curl -X POST http://localhost:8000/admin/sorteios \
  -H "Content-Type: application/json" \
  -d '{
    "status": "ABERTO",
    "premio_base": 1000.00
  }'
```

---

## 6️⃣ Fazer Aposta via Bot Telegram

### No Telegram:
1. Envie `/start` para o bot
2. Clique no botão "🎲 Fazer Aposta"
3. No Mini App:
   - Selecione 20 números brancos
   - Selecione 5 números vermelhos
4. Clique em "CONFIRMAR JOGO"

### Response esperado no Telegram:
```
✅ Aposta registrada com sucesso!

📊 Você selecionou 25 números:
⚪ Brancos: 20
🔴 Powerballs: 5

💰 Valor: R$ 25.00
💵 Saldo restante: R$ 25.00

🎯 Boa sorte no sorteio!
```

✅ **Validações:**
- Saldo foi deduzido (50.00 → 25.00)
- Aposta foi registrada no banco
- Transação tipo APOSTA foi criada

---

## 7️⃣ Testar Saldo Insuficiente

Tente fazer outra aposta (R$ 25.00) com saldo de R$ 25.00.

### Primeira aposta: OK (saldo vira R$ 0.00)
### Segunda tentativa: Deve falhar

### Response esperado:
```
❌ Saldo insuficiente!

💰 Seu saldo: R$ 0.00
💵 Valor da aposta: R$ 25.00
📉 Falta: R$ 25.00

💳 Use /depositar para adicionar saldo à sua carteira.
```

---

## 8️⃣ Ver Minhas Apostas

### Via Bot:
```
/meusJogos
```

### Response esperado:
```
📊 Suas Últimas Apostas

#1 - 🟡 Aguardando sorteio
⚪ 20 brancos | 🔴 5 vermelhos
💰 R$ 25.00
📅 04/12/2025 12:30

#2 - 🟡 Aguardando sorteio
⚪ 20 brancos | 🔴 5 vermelhos
💰 R$ 25.00
📅 04/12/2025 12:15
```

### Via API:
```bash
curl http://localhost:8000/player/my-bets/123456789
```

---

## 9️⃣ Testar Duplicação de Webhook (Segurança)

Tente processar o mesmo pagamento duas vezes:

```bash
# Primeira vez (já processado no passo 2)
curl -X POST http://localhost:8000/finance/test/simulate-payment/PIX_ABC123
```

### Response esperado:
```json
{
  "status": "already_processed",
  "message": "Transação já foi creditada"
}
```

✅ **Validação crítica:**
- Saldo NÃO foi duplicado
- Sistema detectou processamento anterior

---

## 🔟 Ver Estatísticas do Jogador

```bash
curl http://localhost:8000/player/stats/123456789
```

### Response esperado:
```json
{
  "telegram_id": 123456789,
  "nome": "User_123456789",
  "saldo_atual": 0.0,
  "total_apostas": 2,
  "total_gasto": 50.0,
  "total_ganho": 0.0,
  "lucro_liquido": -50.0,
  "total_vitorias": 0,
  "taxa_vitoria": 0.0,
  "apostas_ativas": 2
}
```

---

## 📊 Fluxo Completo - Resumo

```
1. POST /finance/deposit → Cria depósito pendente
2. POST /finance/webhook/pix → Confirma pagamento e credita
3. GET /finance/balance → Verifica saldo creditado
4. Bot /start → Abre Mini App
5. Mini App → Envia aposta
6. Bot verifica saldo → Se OK, deduz e registra
7. GET /player/my-bets → Lista apostas
8. GET /player/stats → Mostra estatísticas
```

---

## ✅ Checklist de Validação

- [ ] Depósito cria transação PENDENTE
- [ ] Webhook credita saldo corretamente
- [ ] Webhook previne duplicação
- [ ] Aposta deduz saldo atomicamente
- [ ] Aposta com saldo insuficiente é rejeitada
- [ ] Histórico mostra todas as transações
- [ ] Estatísticas calculam corretamente
- [ ] Bot mostra saldo atualizado
- [ ] Mini App continua funcionando normalmente

---

## 🐛 Problemas Comuns

### Erro: "Usuário não encontrado"
**Solução:** Envie `/start` no bot primeiro para criar o usuário.

### Erro: "Não há sorteio aberto"
**Solução:** Crie um sorteio com status ABERTO no banco de dados.

### Saldo não atualiza
**Solução:** Verifique se o webhook foi chamado e se o status é "PAID".

### Aposta não funciona
**Solução:** 
1. Verifique se o usuário tem saldo
2. Confirme que há um sorteio ABERTO
3. Veja os logs do servidor para detalhes

---

## 📝 Logs Importantes

Durante os testes, observe os logs do servidor:

```
✓ Depósito criado: Transaction ID 1 - Gateway ID PIX_ABC123 - Valor R$ 50.00
✓ Depósito confirmado: Transaction ID 1 - Usuário João - Valor R$ 50.00 - Novo saldo: R$ 50.00
⚠ Transação 1 já foi processada anteriormente
```

---

## 🎯 Próximos Passos

Após validar todos os testes:
1. Integrar com gateway de pagamento real
2. Adicionar autenticação nos endpoints
3. Implementar rate limiting
4. Adicionar monitoramento e alertas
5. Deploy em produção

