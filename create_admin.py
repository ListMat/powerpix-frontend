"""
Script para criar ou atualizar um usuário admin no banco de dados.
"""
import asyncio
import sys
from database import AsyncSessionLocal, Admin, hash_password
from sqlalchemy import select
from config import get_settings

settings = get_settings()


async def create_admin(username: str = None, password: str = None):
    """
    Cria ou atualiza um admin no banco de dados.
    Se username e password não forem fornecidos, usa as variáveis de ambiente.
    """
    # Usar valores do .env se não fornecidos
    username = username or settings.ADMIN_USERNAME
    password = password or settings.ADMIN_PASSWORD
    
    if not username or not password:
        print("ERRO: Username e password sao obrigatorios")
        print("\nUso:")
        print("  python create_admin.py")
        print("  python create_admin.py <username> <password>")
        sys.exit(1)
    
    async with AsyncSessionLocal() as session:
        try:
            # Verificar se admin já existe
            result = await session.execute(
                select(Admin).where(Admin.username == username)
            )
            admin = result.scalar_one_or_none()
            
            if admin:
                # Atualizar senha existente
                admin.password_hash = hash_password(password)
                await session.commit()
                print(f"OK: Admin '{username}' atualizado com sucesso!")
                print(f"   Senha alterada para a nova senha fornecida.")
            else:
                # Criar novo admin
                password_hash = hash_password(password)
                new_admin = Admin(
                    username=username,
                    password_hash=password_hash
                )
                session.add(new_admin)
                await session.commit()
                print(f"OK: Admin '{username}' criado com sucesso!")
            
        except Exception as e:
            await session.rollback()
            print(f"ERRO ao criar/atualizar admin: {e}")
            sys.exit(1)


async def list_admins():
    """Lista todos os admins cadastrados"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Admin))
            admins = result.scalars().all()
            
            if not admins:
                print("Nenhum admin cadastrado no banco de dados.")
            else:
                print(f"Admins cadastrados ({len(admins)}):")
                for admin in admins:
                    print(f"   - {admin.username} (ID: {admin.id})")
        except Exception as e:
            print(f"ERRO ao listar admins: {e}")
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Sem argumentos: usar variáveis de ambiente
        print("Criando admin usando variaveis do .env...")
        print(f"   Username: {settings.ADMIN_USERNAME}")
        print(f"   Password: {'*' * len(settings.ADMIN_PASSWORD)}")
        asyncio.run(create_admin())
    elif len(sys.argv) == 2 and sys.argv[1] == "--list":
        # Listar admins
        asyncio.run(list_admins())
    elif len(sys.argv) == 3:
        # Com username e password
        username = sys.argv[1]
        password = sys.argv[2]
        print(f"Criando admin '{username}'...")
        asyncio.run(create_admin(username, password))
    else:
        print("Uso incorreto!")
        print("\nOpcoes:")
        print("  python create_admin.py              # Usa ADMIN_USERNAME e ADMIN_PASSWORD do .env")
        print("  python create_admin.py <user> <pwd> # Cria admin com username e password especificos")
        print("  python create_admin.py --list       # Lista todos os admins cadastrados")
        sys.exit(1)

