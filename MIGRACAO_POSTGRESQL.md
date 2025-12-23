# Migração para PostgreSQL

## Status
✅ **Migração concluída!**

O projeto foi migrado de SQLite para PostgreSQL.

## Configuração

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

Isso instalará o `asyncpg` (driver PostgreSQL async) no lugar de `aiosqlite`.

### 2. Configurar PostgreSQL

Certifique-se de que o PostgreSQL está rodando localmente e crie o banco de dados:

```sql
CREATE DATABASE powerpix;
```

Ou via linha de comando:
```bash
createdb powerpix
```

### 3. Configurar variáveis de ambiente

Crie ou atualize o arquivo `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:SUA_SENHA@localhost:5432/powerpix
```

**Formato da URL:**
```
postgresql+asyncpg://USUARIO:SENHA@HOST:PORTA/NOME_DO_BANCO
```

**Exemplos:**
- Usuário padrão: `postgresql+asyncpg://postgres:postgres@localhost:5432/powerpix`
- Com senha personalizada: `postgresql+asyncpg://postgres:minhasenha123@localhost:5432/powerpix`
- Porta diferente: `postgresql+asyncpg://postgres:postgres@localhost:5433/powerpix`

### 4. Executar a aplicação

A primeira vez que rodar, o SQLAlchemy criará todas as tabelas automaticamente:

```bash
python app.py
```

## Migração de dados (se necessário)

Se você já tem dados no SQLite e quer migrá-los para PostgreSQL, use uma ferramenta como:

- **pgloader**: `pgloader sqlite:///path/to/powerpix.db postgresql://postgres:senha@localhost/powerpix`
- **Python script**: Crie um script que leia do SQLite e escreva no PostgreSQL

## Diferenças SQLite vs PostgreSQL

### Tipos de dados:
- `REAL` → `DOUBLE PRECISION`
- `BOOLEAN DEFAULT 0` → `BOOLEAN DEFAULT FALSE`
- `DATETIME` → `TIMESTAMP`

### Consultas:
- `PRAGMA table_info(table)` → `information_schema.columns` (PostgreSQL)
- Removido uso de PRAGMA (específico do SQLite)

## Verificação

Para verificar se está conectado corretamente:

```python
from database import engine
async with engine.connect() as conn:
    result = await conn.execute(text("SELECT version()"))
    print(result.fetchone())
```

Se funcionar, você verá a versão do PostgreSQL!

## Troubleshooting

### Erro: "password authentication failed"
- Verifique a senha do PostgreSQL no `.env`
- Teste a conexão: `psql -U postgres -d powerpix`

### Erro: "database does not exist"
- Crie o banco: `CREATE DATABASE powerpix;`

### Erro: "asyncpg not found"
- Instale: `pip install asyncpg`

