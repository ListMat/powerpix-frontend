"""Script para criar um jogador de teste"""
import asyncio
from database import AsyncSessionLocal, Usuario
from sqlalchemy import select
from datetime import datetime

async def create_test_player():
    """Cria um jogador de teste"""
    async with AsyncSessionLocal() as session:
        try:
            # Dados do jogador de teste
            telegram_id = 123456789  # Altere para o seu Telegram ID
            nome = "Jogador Teste"
            cpf = "123.456.789-00"
            pix = "teste@email.com"
            telefone = "(11) 99999-9999"
            cidade = "São Paulo"
            estado = "SP"
            
            # Verificar se o jogador já existe
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"\nAVISO: Jogador com Telegram ID {telegram_id} ja existe!")
                print(f"   Nome: {existing_user.nome}")
                print(f"   ID: {existing_user.id}")
                return
            
            # Criar novo jogador
            novo_jogador = Usuario(
                telegram_id=telegram_id,
                nome=nome,
                cpf=cpf,
                pix=pix,
                telefone=telefone,
                cidade=cidade,
                estado=estado,
                saldo=0.0,
                cadastro_completo=True,
                data_cadastro=datetime.utcnow()
            )
            
            session.add(novo_jogador)
            await session.commit()
            await session.refresh(novo_jogador)
            
            print("=" * 80)
            print("Jogador de Teste Criado com Sucesso!")
            print("=" * 80)
            print(f"   ID: {novo_jogador.id}")
            print(f"   Telegram ID: {novo_jogador.telegram_id}")
            print(f"   Nome: {novo_jogador.nome}")
            print(f"   CPF: {novo_jogador.cpf}")
            print(f"   PIX: {novo_jogador.pix}")
            print(f"   Telefone: {novo_jogador.telefone}")
            print(f"   Cidade: {novo_jogador.cidade}")
            print(f"   Estado: {novo_jogador.estado}")
            print(f"   Saldo: R$ {novo_jogador.saldo:.2f}")
            print(f"   Cadastro Completo: {novo_jogador.cadastro_completo}")
            print("=" * 80)
            
        except Exception as e:
            await session.rollback()
            print(f"\nERRO ao criar jogador: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("\nNOTA: Este script cria um jogador de teste com Telegram ID 123456789.")
    print("      Para criar um jogador com seus dados, edite o arquivo e altere")
    print("      o telegram_id e os outros dados antes de executar.\n")
    
    resposta = input("Deseja continuar? (s/n): ").strip().lower()
    if resposta == 's':
        asyncio.run(create_test_player())
    else:
        print("Operacao cancelada.")
        print("\nPara criar um jogador personalizado, use:")
        print("  python create_player.py <telegram_id> <nome> [cpf] [pix] [telefone] [cidade] [estado]")
        print("\nExemplo:")
        print("  python create_player.py 987654321 'Joao Silva' '123.456.789-00' 'joao@email.com' '(11) 99999-9999' 'Sao Paulo' 'SP'")

