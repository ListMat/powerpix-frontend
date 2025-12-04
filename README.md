# PowerPix Frontend - Mini App Telegram

Frontend do Mini App PowerPix para deploy no Vercel.

## 📋 Como fazer o Deploy no Vercel

### Passo 1: Criar Repositório no GitHub

1. Acesse [GitHub.com](https://github.com) e faça login
2. Clique no **+** no canto superior direito → **"New repository"**
3. Nomeie como `powerpix-frontend`
4. Marque como **Public**
5. Clique em **"Create repository"**

### Passo 2: Fazer Upload dos Arquivos

1. Na tela do repositório criado, clique em **"uploading an existing file"**
2. Arraste o arquivo `index.html` para lá
3. Clique em **"Commit changes"** (botão verde)

### Passo 3: Conectar no Vercel

1. Acesse [vercel.com](https://vercel.com) e faça login (pode usar sua conta do GitHub)
2. No Dashboard, clique em **"Add New..."** → **"Project"**
3. Na esquerda, procure **"Import Git Repository"**
4. Procure `powerpix-frontend` na lista e clique em **"Import"**

### Passo 4: Configurar o Projeto

Na tela de configuração:

- **Framework Preset**: Deixe em **"Other"** (é HTML puro)
- **Root Directory**: Deixe como `./`
- Clique em **"Deploy"** (botão azul grande)

### Passo 5: Obter a URL

1. Após o deploy (uns 15 segundos), você verá confetes 🎉
2. Clique em **"Continue to Dashboard"**
3. No topo da tela, você verá o campo **"Domains"**
4. Será algo como: `powerpix-frontend.vercel.app`
5. **Copie esse link** - essa é a URL que você vai usar no BotFather

## 🔄 Atualizando o Site

Sempre que quiser atualizar o site:

1. Edite o arquivo `index.html` no seu computador
2. Faça commit e push para o GitHub
3. O Vercel detecta automaticamente e atualiza o site em segundos

## 📝 Nota Importante

Este é apenas o **frontend** (a interface visual). O **backend** (Python/FastAPI) precisa ser hospedado separadamente em serviços como:
- Render.com
- Railway.app
- Heroku
- Ou manter rodando localmente com ngrok para desenvolvimento

## 🔗 Configuração no BotFather

Depois de obter a URL do Vercel, configure no BotFather:

1. Envie `/newapp` para o @BotFather
2. Selecione seu bot
3. Quando pedir a URL, envie: `https://powerpix-frontend.vercel.app` (ou a URL que você recebeu)

