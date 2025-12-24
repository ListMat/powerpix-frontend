"""Script para verificar usuários no banco de dados"""
import asyncio
from database import AsyncSessionLocal, Usuario
from sqlalchemy import select

async def check_users():
    """Verifica usuários cadastrados"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario))
        usuarios = result.scalars().all()
        
        print(f"\nTotal de usuários: {len(usuarios)}")
        print("-" * 80)
        
        for usuario in usuarios:
            print(f"ID: {usuario.id}")
            print(f"Telegram ID: {usuario.telegram_id}")
            print(f"Nome: {usuario.nome or 'N/A'}")
            print(f"CPF: {usuario.cpf or 'N/A'}")
            print(f"PIX: {usuario.pix or 'N/A'}")
            print(f"Telefone: {usuario.telefone or 'N/A'}")
            print(f"Cadastro Completo: {usuario.cadastro_completo}")
            print(f"Data Cadastro: {usuario.data_cadastro}")
            print("-" * 80)

if __name__ == "__main__":
    asyncio.run(check_users())

