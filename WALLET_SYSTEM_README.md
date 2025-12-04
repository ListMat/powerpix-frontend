# Sistema de Carteira (Wallet) - PowerPix

## 📋 Visão Geral

Sistema completo de carteira digital integrado ao PowerPix, onde usuários depositam saldo via Pix e usam esse saldo para fazer apostas.

## 🏗️ Arquitetura

### 1. Database Models (database.py)

#### Novos Enums:
- `TipoTransacao`: DEPOSITO, APOSTA, PREMIO, SAQUE
- `StatusTransacao`: PENDENTE, PAGO, FALHA, CANCELADO

#### Novo Model: Transacao
```python
class Transacao:
    - usuario_id: FK para Usuario
    - tipo: Enum (TipoTransacao)
    - valor: Float
    - status: Enum (StatusTransacao)
    - gateway_id: String (ID da transação no gateway de pagamento)
    - descricao: Text
    - created_at: DateTime
    - updated_at: DateTime
```

#### Atualização no Usuario:
- Campo `saldo` já existia, agora é obrigatório (nullable=False)
- Relacionamento com `transacoes`

---

## 🚀 Endpoints da API

### Finance Router (`/finance`)

#### 1. POST /finance/deposit
**Cria uma solicitação de depósito via Pix**

Request:
```json
{
  "telegram_id": 123456789,
  "valor": 50.00
}
```

Response:
```json
{
  "transaction_id": 1,
  "pix_code": "00020126580014br.gov.bcb.pix...",
  "valor": 50.00,
  "status": "PENDENTE",
  "created_at": "2025-12-04T12:00:00"
}
```

**Fluxo:**
1. Busca o usuário
2. Gera um gateway_id único (simulação)
3. Cria registro de transação com status PENDENTE
4. Retorna código Pix (mock) para o usuário pagar

---

#### 2. POST /finance/webhook/pix
**Webhook chamado pelo gateway quando o Pix é confirmado**

Request:
```json
{
  "gateway_id": "PIX_ABC123",
  "status": "PAID",
  "valor": 50.00
}
```

**Segurança implementada:**
- ✅ Verifica se transação já foi processada (evita duplicação)
- ✅ Usa transação atômica para garantir consistência
- ✅ Valida status antes de creditar

**Fluxo:**
1. Busca transação pelo gateway_id
2. Verifica se já foi processada (CRÍTICO!)
3. Se status = PAID:
   - Atualiza transação para PAGO
   - Credita saldo no usuário
   - Commit atômico
4. Retorna confirmação

---

#### 3. GET /finance/balance/{telegram_id}
**Retorna o saldo atual do usuário**

Response:
```json
{
  "telegram_id": 123456789,
  "nome": "João Silva",
  "saldo": 125.50
}
```

---

#### 4. GET /finance/transactions/{telegram_id}
**Histórico de transações**

Response:
```json
{
  "telegram_id": 123456789,
  "transactions": [
    {
      "id": 1,
      "tipo": "DEPOSITO",
      "valor": 50.00,
      "status": "PAGO",
      "descricao": "Depósito via Pix - R$ 50.00",
      "created_at": "2025-12-04T12:00:00",
      "updated_at": "2025-12-04T12:05:00"
    }
  ]
}
```

---

#### 5. POST /finance/test/simulate-payment/{gateway_id}
**APENAS PARA TESTES - Simula pagamento de Pix**

⚠️ **REMOVER EM PRODUÇÃO!**

---

### Player Router (`/player`)

#### 1. GET /player/my-bets/{telegram_id}
**Retorna todas as apostas do usuário**

Response:
```json
{
  "telegram_id": 123456789,
  "nome": "João Silva",
  "total_apostas": 5,
  "jogos_ativos": [
    {
      "id": 10,
      "numeros_brancos": [1, 5, 12, ...],
      "numeros_vermelhos": [3, 7, ...],
      "valor_pago": 25.00,
      "data_aposta": "2025-12-04T12:00:00",
      "sorteio_id": 5,
      "sorteio_status": "ABERTO",
      "status_display": "AGUARDANDO"
    }
  ],
  "historico": [
    {
      "id": 9,
      "status_display": "GANHOU",
      "valor_premio": 100.00,
      "acertos": 15
    }
  ]
}
```

**Status Display:**
- `AGUARDANDO`: Sorteio ainda não realizado
- `GANHOU`: Aposta vencedora
- `PERDEU`: Aposta não vencedora

---

#### 2. GET /player/results/{draw_id}
**Resultados de um sorteio específico**

Query param: `telegram_id`

Response:
```json
{
  "sorteio_id": 5,
  "data_sorteio": "2025-12-04T18:00:00",
  "status": "FECHADO",
  "numeros_sorteados_brancos": [2, 7, 15, ...],
  "numeros_sorteados_vermelhos": [1, 5, ...],
  "apostas_usuario": [...]
}
```

---

#### 3. GET /player/stats/{telegram_id}
**Estatísticas do jogador**

Response:
```json
{
  "telegram_id": 123456789,
  "nome": "João Silva",
  "saldo_atual": 125.50,
  "total_apostas": 20,
  "total_gasto": 500.00,
  "total_ganho": 300.00,
  "lucro_liquido": -200.00,
  "total_vitorias": 3,
  "taxa_vitoria": 15.0,
  "apostas_ativas": 2
}
```

---

## 🤖 Comandos do Bot Telegram

### Novos comandos:

#### /start
- Cria usuário se não existir
- Mostra botões: Fazer Aposta, Ver Saldo, Meus Jogos

#### /saldo
- Mostra saldo atual
- Instruções para depositar

#### /depositar
- Instruções para fazer depósito
- (Pode ser expandido para iniciar depósito direto)

#### /meusJogos
- Lista últimas 10 apostas
- Mostra status de cada uma
- Números escolhidos

---

## 🔒 Lógica de Aposta (Atualizada)

Quando o usuário envia a aposta do Mini App:

1. ✅ Valida sorteio ABERTO
2. ✅ Busca/cria usuário
3. ✅ Calcula valor da aposta
4. ✅ **VERIFICA SALDO** ← NOVO!
5. ✅ Se saldo insuficiente: retorna erro
6. ✅ Se saldo ok:
   - Deduz do saldo (atomicamente)
   - Cria transação tipo APOSTA
   - Cria registro da aposta
   - Commit único
7. ✅ Retorna confirmação com saldo restante

### Mensagem de saldo insuficiente:
```
❌ Saldo insuficiente!

💰 Seu saldo: R$ 5.00
💵 Valor da aposta: R$ 25.00
📉 Falta: R$ 20.00

💳 Use /depositar para adicionar saldo à sua carteira.
```

---

## 🧪 Como Testar

### 1. Criar depósito:
```bash
curl -X POST http://localhost:8000/finance/deposit \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 123456789, "valor": 50.00}'
```

Response contém `gateway_id` e `transaction_id`.

### 2. Simular pagamento (TESTE):
```bash
curl -X POST http://localhost:8000/finance/test/simulate-payment/PIX_ABC123
```

### 3. Verificar saldo:
```bash
curl http://localhost:8000/finance/balance/123456789
```

### 4. Fazer aposta no Telegram:
- Envie `/start` para o bot
- Clique em "Fazer Aposta"
- Selecione números
- Confirme (será deduzido do saldo)

### 5. Ver apostas:
```bash
curl http://localhost:8000/player/my-bets/123456789
```

---

## ⚠️ Pontos de Atenção em Produção

### 1. Integração de Pagamento Real
Substituir o mock do Pix por integração real:
- Mercado Pago
- PagSeguro
- Banco do Brasil
- Outros gateways

### 2. Webhook Security
Adicionar validação de assinatura:
```python
def verify_webhook_signature(payload, signature, secret):
    # Implementar verificação HMAC ou JWT
    pass
```

### 3. Remover endpoint de teste:
```python
# REMOVER EM PRODUÇÃO
@router.post("/test/simulate-payment/{gateway_id}")
```

### 4. Rate Limiting
Adicionar proteção contra abuso:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/deposit")
@limiter.limit("5/minute")
async def create_deposit(...):
```

### 5. Logs e Monitoramento
- Alertas para transações pendentes antigas
- Monitorar tentativas de duplicação
- Tracking de sucesso/falha de webhooks

### 6. Tratamento de Concorrência
O sistema já usa transações atômicas, mas considere:
- Lock otimista se múltiplos processos
- Fila de processamento para webhooks

---

## 📊 Fluxo Completo

```
1. Usuário entra no bot → /start
2. Verifica saldo → R$ 0.00
3. Clica /depositar → POST /finance/deposit
4. Recebe código Pix → Paga no banco
5. Gateway confirma → POST /finance/webhook/pix
6. Sistema credita saldo → R$ 50.00
7. Usuário faz aposta → Mini App
8. Sistema deduz saldo → R$ 25.00 (restante)
9. Aposta registrada → Aguardando sorteio
10. Sorteio realizado → Se ganhar, recebe prêmio no saldo
```

---

## 🎯 Próximas Funcionalidades

- [ ] Sistema de saque
- [ ] Notificações de depósito confirmado
- [ ] Botão "Depositar" integrado no bot
- [ ] QR Code para Pix
- [ ] Histórico detalhado com filtros
- [ ] Relatório de ganhos/perdas
- [ ] Sistema de bônus e promoções

