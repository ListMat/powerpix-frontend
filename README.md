# PowerPix - Sistema de Loteria

Sistema completo de loteria com Telegram Mini App e Painel Administrativo.

## 🚀 Tecnologias

- **Backend**: FastAPI + Aiogram 3.x
- **Database**: SQLite (aiosqlite) / SQLAlchemy async
- **Frontend**: HTML/JS (Telegram Mini App) + Jinja2 Templates (Admin)
- **Autenticação**: JWT com cookies

## 📋 Pré-requisitos

- Python 3.11+
- Token do Bot Telegram (obtenha em @BotFather)

## 🔧 Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o arquivo `.env`:
```env
BOT_TOKEN=seu_token_aqui
WEBHOOK_URL=https://seu-dominio.com
WEBHOOK_PATH=/webhook
SECRET_KEY=gere_uma_chave_secreta_aqui
ADMIN_USERNAME=admin
ADMIN_PASSWORD=senha_forte
DATABASE_URL=sqlite+aiosqlite:///powerpix.db
VALOR_APOSTA=5.00
```

Para gerar uma SECRET_KEY:
```bash
openssl rand -hex 32
```

## 🏃 Executando

### Desenvolvimento (Polling)
Para desenvolvimento local, você pode usar polling ao invés de webhook:

```bash
python app.py
```

Ou com uvicorn diretamente:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Produção (Webhook)
1. Configure o `WEBHOOK_URL` no `.env` com sua URL pública
2. Use um serviço como ngrok para desenvolvimento:
```bash
ngrok http 8000
```
3. Atualize o `WEBHOOK_URL` no `.env` com a URL do ngrok
4. Inicie o servidor:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## 📱 Uso

### Bot Telegram
1. Envie `/start` para o bot
2. Clique no botão "Abrir PowerPix"
3. Selecione seus números e confirme a aposta

### Painel Admin
1. Acesse `http://localhost:8000/admin/login`
2. Faça login com as credenciais do `.env`
3. Visualize o dashboard com:
   - Total arrecadado
   - Lucro da casa (30% até R$ 3.000, depois 90% sobre excedente)
   - Fundo para prêmios
   - Lista de apostas
4. Gerencie sorteios (criar/encerrar)

## 📊 Lógica Financeira

- **Até R$ 3.000**: Lucro da casa = 30% da arrecadação
- **Acima de R$ 3.000**: Lucro da casa = 30% dos primeiros R$ 3.000 + 90% do excedente
- **Fundo para Prêmios**: Arrecadação - Lucro da Casa

## 🔒 Segurança

- JWT com expiração de 24h
- Cookies HttpOnly
- Senhas hasheadas com bcrypt
- Validação de token no webhook

## 📁 Estrutura

```
/powerpix
  ├── app.py              # Entry point
  ├── config.py           # Configurações
  ├── database.py         # Models e DB
  ├── routers/
  │   ├── bot.py         # Handlers do Telegram
  │   ├── webapp.py      # Mini App
  │   └── admin.py       # Painel admin
  ├── templates/         # Templates HTML
  └── static/            # Arquivos estáticos
```

## 🐛 Troubleshooting

- **Webhook não funciona**: Verifique se `WEBHOOK_URL` está correto e acessível
- **Erro de autenticação**: Verifique `SECRET_KEY` no `.env`
- **Banco não inicializa**: Verifique permissões de escrita no diretório

