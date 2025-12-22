# 🚀 Comandos Git para Upload no GitHub

Se você preferir usar a linha de comando ao invés da interface web do GitHub:

## Primeira vez (criar repositório)

1. **Navegue até a pasta:**
   ```bash
   cd powerpix-front
   ```

2. **Inicialize o Git:**
   ```bash
   git init
   ```

3. **Adicione os arquivos:**
   ```bash
   git add .
   ```

4. **Faça o primeiro commit:**
   ```bash
   git commit -m "Initial commit - PowerPix Frontend"
   ```

5. **Crie o repositório no GitHub** (via interface web) e depois conecte:
   ```bash
   git remote add origin https://github.com/SEU_USUARIO/powerpix-frontend.git
   git branch -M main
   git push -u origin main
   ```

## Atualizações futuras

Sempre que fizer alterações no `index.html`:

```bash
cd powerpix-front
git add .
git commit -m "Atualização do frontend"
git push
```

O Vercel detectará automaticamente e fará o redeploy! 🎉

