"""
Script para testar conexão com o banco de dados PostgreSQL
"""
import asyncio
from database import engine, AsyncSessionLocal
from sqlalchemy import text
from config import get_settings

settings = get_settings()


async def test_connection():
    """Testa a conexão com o banco de dados"""
    print("=" * 50)
    print("Teste de Conexão com Banco de Dados")
    print("=" * 50)
    print(f"\nDATABASE_URL: {settings.DATABASE_URL}")
    print(f"Tipo: {'PostgreSQL' if 'postgresql' in settings.DATABASE_URL.lower() else 'SQLite'}")
    print("\n" + "-" * 50)
    
    try:
        # Teste 1: Conectar ao banco
        print("\n1. Testando conexão...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"   OK: Conectado com sucesso!")
            print(f"   Versão do PostgreSQL: {version.split(',')[0]}")
        
        # Teste 2: Verificar se as tabelas existem
        print("\n2. Verificando tabelas...")
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"   OK: {len(tables)} tabela(s) encontrada(s):")
                for table in tables:
                    print(f"      - {table}")
            else:
                print("   AVISO: Nenhuma tabela encontrada")
        
        # Teste 3: Verificar usuários cadastrados
        print("\n3. Verificando usuários cadastrados...")
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            from database import Usuario
            
            result = await session.execute(select(Usuario))
            usuarios = result.scalars().all()
            
            if usuarios:
                print(f"   OK: {len(usuarios)} usuario(s) encontrado(s):")
                for usuario in usuarios[:5]:  # Mostrar apenas os 5 primeiros
                    print(f"      - ID: {usuario.id}, Telegram ID: {usuario.telegram_id}, Nome: {usuario.nome or 'Sem nome'}")
                if len(usuarios) > 5:
                    print(f"      ... e mais {len(usuarios) - 5} usuario(s)")
            else:
                print("   AVISO: Nenhum usuário cadastrado")
        
        # Teste 4: Verificar admins cadastrados
        print("\n4. Verificando admins cadastrados...")
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            from database import Admin
            
            result = await session.execute(select(Admin))
            admins = result.scalars().all()
            
            if admins:
                print(f"   OK: {len(admins)} admin(s) encontrado(s):")
                for admin in admins:
                    print(f"      - ID: {admin.id}, Username: {admin.username}")
            else:
                print("   AVISO: Nenhum admin cadastrado")
        
        # Teste 5: Verificar estrutura da tabela usuarios
        print("\n5. Verificando estrutura da tabela usuarios...")
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'usuarios'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            
            if columns:
                print(f"   OK: {len(columns)} coluna(s) encontrada(s):")
                for col in columns:
                    nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                    print(f"      - {col[0]}: {col[1]} ({nullable})")
            else:
                print("   AVISO: Tabela 'usuarios' não encontrada")
        
        print("\n" + "=" * 50)
        print("Teste concluído com sucesso!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nERRO: Falha na conexão ou operação")
        print(f"Detalhes: {str(e)}")
        print("\n" + "=" * 50)
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("\n")
    success = asyncio.run(test_connection())
    if success:
        print("\nBanco de dados está funcionando corretamente!")
    else:
        print("\nVerifique a configuração do DATABASE_URL no arquivo .env")
        print("\nExemplo de configuração PostgreSQL:")
        print("DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost:5432/nome_do_banco")
        print("\nExemplo de configuração SQLite:")
        print("DATABASE_URL=sqlite+aiosqlite:///./powerpix.db")

