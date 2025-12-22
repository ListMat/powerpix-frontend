# 🧪 Guia de Teste - Sistema de Depósito PIX

## ✅ Implementações Concluídas

### 1. Banco de Dados
- ✅ Campo `cpf` adicionado à tabela `usuarios`
- ✅ Migração automática configurada em `database.py`

### 2. Cadastro de Usuário
- ✅ Formulário atualizado com campo CPF obrigatório
- ✅ Máscara automática para CPF (000.000.000-00)
- ✅ Validação de CPF no frontend
- ✅ Bot processa cadastro com CPF

### 3. Tela de Depósito
- ✅ Interface completa no Mini App
- ✅ Exibição de saldo atual
- ✅ Botões de valor rápido (R$ 10, 25, 50, 100)
- ✅ Geração de QR Code PIX via Asaas
- ✅ Código PIX "Copia e Cola"
- ✅ Botão para copiar código

### 4. Integração Backend
- ✅ Endpoint `/finance/deposit` criando cobrança no Asaas
- ✅ Cliente Asaas criado automaticamente com CPF
- ✅ Webhook `/finance/webhook/asaas` processando pagamentos
- ✅ Crédito automático de saldo após confirmação

---

## 🧪 Como Testar

### Passo 1: Configurar Ambiente Asaas

1. **Criar conta no Asaas (Sandbox)**:
   - Acesse: https://www.asaas.com/
   - Crie uma conta de testes
   - Acesse: https://sandbox.asaas.com/

2. **Obter API Key**:
   - No painel Asaas Sandbox, vá em **Integrações** → **API Key**
   - Copie a chave (formato: `$aact_...`)

3. **Configurar `.env`**:
   ```env
   # Asaas Configuration
   ASAAS_API_KEY=$aact_YourSandboxKeyHere
   ASAAS_API_URL=https://sandbox.asaas.com/api/v3
   ASAAS_WEBHOOK_TOKEN=seu_token_secreto_aqui
   ```

4. **Configurar Webhook no Asaas**:
   - No painel Asaas, vá em **Integrações** → **Webhooks**
   - Adicione: `https://seu-dominio.com/finance/webhook/asaas`
   - Eventos: `PAYMENT_RECEIVED`, `PAYMENT_CONFIRMED`

### Passo 2: Iniciar o Sistema

```bash
# Instalar dependências (se ainda não fez)
pip install -r requirements.txt

# Iniciar o servidor
python app.py
```

### Passo 3: Testar Cadastro

1. Abra o bot no Telegram
2. Envie `/start`
3. Clique em "Fazer Cadastro"
4. Preencha:
   - Nome: `João da Silva`
   - CPF: `123.456.789-00` (CPF de teste válido)
   - PIX: `joao@email.com`
   - Telefone: `(11) 98765-4321`
   - Cidade/Estado: (opcional)
5. Clique em "Concluir Cadastro"
6. Verifique se recebeu confirmação no bot

### Passo 4: Testar Depósito

1. No Mini App, clique no botão **"💰 Depositar"**
2. Verifique se o saldo atual aparece (R$ 0,00)
3. Digite um valor (ex: R$ 10,00) ou clique em um botão rápido
4. Clique em **"💳 GERAR PIX"**
5. Verifique se:
   - QR Code aparece na tela
   - Código PIX "Copia e Cola" está visível
   - Mensagem "Aguardando pagamento..." aparece

### Passo 5: Simular Pagamento (Sandbox)

**Opção A: Via Painel Asaas (Recomendado)**
1. Acesse o painel Asaas Sandbox
2. Vá em **Cobranças** → **Todas as cobranças**
3. Encontre a cobrança recém-criada
4. Clique em **"Confirmar Recebimento"**

**Opção B: Via Endpoint de Teste (Desenvolvimento)**
```bash
# Obtenha o payment_id da cobrança (aparece no log do servidor)
curl -X POST http://localhost:8000/finance/test/simulate-payment/{payment_id}
```

### Passo 6: Verificar Crédito

1. Aguarde alguns segundos (webhook processa)
2. No Mini App, verifique se:
   - Saldo foi atualizado automaticamente
   - Aparece o novo valor (ex: R$ 10,00)
3. Volte para a tela de apostas
4. Confirme que o saldo aparece no topo

---

## 🔍 Verificações de Segurança

### 1. Idempotência do Webhook
- ✅ Transação só é creditada uma vez (verificação de status)
- ✅ Pagamentos duplicados são ignorados

### 2. Validação de CPF
- ✅ Frontend valida CPF antes de enviar
- ✅ Backend requer CPF para criar depósito

### 3. Atomicidade
- ✅ Saldo é creditado em transação atômica
- ✅ Rollback automático em caso de erro

---

## 📊 Logs para Monitorar

Ao testar, observe os logs do servidor:

```
INFO - Depósito Asaas criado: Transaction ID 1 - Payment ID chr_xxx - Valor R$ 10.00
INFO - Webhook Asaas recebido: PAYMENT_RECEIVED
INFO - ✓ Depósito Asaas confirmado: Transaction ID 1 - Usuário João da Silva - Valor R$ 10.00 - Novo saldo: R$ 10.00
```

---

## 🐛 Troubleshooting

### Erro: "CPF não cadastrado"
- **Solução**: Complete o cadastro no Mini App com CPF válido

### Erro: "Usuário não encontrado"
- **Solução**: Envie `/start` no bot primeiro

### QR Code não aparece
- **Solução**: Verifique se `ASAAS_API_KEY` está configurado corretamente

### Saldo não atualiza após pagamento
- **Solução**: 
  1. Verifique se webhook está configurado no Asaas
  2. Confirme que a URL do webhook está acessível
  3. Veja os logs do servidor para erros

### Erro 403 no webhook
- **Solução**: Descomente a validação de token em `routers/finance.py` (linha 166)

---

## 🚀 Próximos Passos (Produção)

1. **Trocar para API de Produção**:
   ```env
   ASAAS_API_URL=https://api.asaas.com/v3
   ASAAS_API_KEY=$aact_YourProductionKeyHere
   ```

2. **Ativar validação de webhook**:
   - Descomente as linhas 166-168 em `routers/finance.py`
   - Configure `ASAAS_WEBHOOK_TOKEN` no `.env`

3. **Configurar HTTPS**:
   - Webhook Asaas requer HTTPS em produção
   - Use Nginx + Let's Encrypt ou Cloudflare

4. **Monitoramento**:
   - Configure alertas para falhas de webhook
   - Monitore transações pendentes há mais de 30 minutos

---

## 📝 Checklist Final

- [ ] Asaas Sandbox configurado
- [ ] API Key no `.env`
- [ ] Webhook configurado no painel Asaas
- [ ] Servidor rodando
- [ ] Cadastro completo testado
- [ ] Depósito criado com sucesso
- [ ] QR Code gerado
- [ ] Pagamento simulado
- [ ] Saldo creditado automaticamente
- [ ] Logs sem erros

---

## 🎉 Sucesso!

Se todos os passos funcionaram, o sistema de depósito está **100% operacional**! 

O fluxo completo é:
1. Usuário se cadastra (com CPF)
2. Clica em "Depositar"
3. Escolhe valor e gera PIX
4. Paga via QR Code ou Copia e Cola
5. Saldo é creditado automaticamente
6. Pode fazer apostas imediatamente

**Pronto para produção!** 🚀

