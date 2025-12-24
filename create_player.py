"""Script para criar um jogador manualmente no banco de dados"""
import asyncio
import sys
from database import AsyncSessionLocal, Usuario
from sqlalchemy import select
from datetime import datetime

async def create_player(telegram_id: int, nome: str, cpf: str = None, pix: str = None, telefone: str = None, cidade: str = None, estado: str = None):
    """Cria um novo jogador no banco de dados"""
    async with AsyncSessionLocal() as session:
        try:
            # Verificar se o jogador já existe
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"\nAVISO: Jogador com Telegram ID {telegram_id} ja existe!")
                print(f"   Nome: {existing_user.nome}")
                print(f"   Cadastro Completo: {existing_user.cadastro_completo}")
                
                resposta = input("\nDeseja atualizar os dados? (s/n): ").strip().lower()
                if resposta != 's':
                    print("Operacao cancelada.")
                    return
                
                # Atualizar dados existentes
                existing_user.nome = nome
                if cpf:
                    existing_user.cpf = cpf
                if pix:
                    existing_user.pix = pix
                if telefone:
                    existing_user.telefone = telefone
                if cidade:
                    existing_user.cidade = cidade
                if estado:
                    existing_user.estado = estado
                
                # Verificar se cadastro está completo
                cadastro_completo = bool(nome and cpf and pix and telefone)
                existing_user.cadastro_completo = cadastro_completo
                
                await session.commit()
                print(f"\nOK: Jogador atualizado com sucesso!")
                print(f"   ID: {existing_user.id}")
                print(f"   Telegram ID: {existing_user.telegram_id}")
                print(f"   Nome: {existing_user.nome}")
                print(f"   Cadastro Completo: {existing_user.cadastro_completo}")
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
                cadastro_completo=bool(nome and cpf and pix and telefone),
                data_cadastro=datetime.utcnow()
            )
            
            session.add(novo_jogador)
            await session.commit()
            await session.refresh(novo_jogador)
            
            print(f"\nOK: Jogador criado com sucesso!")
            print(f"   ID: {novo_jogador.id}")
            print(f"   Telegram ID: {novo_jogador.telegram_id}")
            print(f"   Nome: {novo_jogador.nome}")
            print(f"   CPF: {novo_jogador.cpf or 'N/A'}")
            print(f"   PIX: {novo_jogador.pix or 'N/A'}")
            print(f"   Telefone: {novo_jogador.telefone or 'N/A'}")
            print(f"   Cidade: {novo_jogador.cidade or 'N/A'}")
            print(f"   Estado: {novo_jogador.estado or 'N/A'}")
            print(f"   Saldo: R$ {novo_jogador.saldo:.2f}")
            print(f"   Cadastro Completo: {novo_jogador.cadastro_completo}")
            
        except Exception as e:
            await session.rollback()
            print(f"\nERRO ao criar/atualizar jogador: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

async def interactive_create():
    """Cria um jogador de forma interativa"""
    print("=" * 80)
    print("Criar Novo Jogador")
    print("=" * 80)
    
    try:
        telegram_id = int(input("\nTelegram ID (obrigatorio): ").strip())
        nome = input("Nome completo (obrigatorio): ").strip()
        
        if not nome:
            print("ERRO: Nome e obrigatorio!")
            return
        
        cpf = input("CPF (opcional, formato: 000.000.000-00): ").strip() or None
        pix = input("Chave PIX (opcional): ").strip() or None
        telefone = input("Telefone (opcional, formato: (00) 00000-0000): ").strip() or None
        cidade = input("Cidade (opcional): ").strip() or None
        estado = input("Estado/UF (opcional, 2 letras): ").strip() or None
        
        if estado and len(estado) > 2:
            estado = estado[:2].upper()
        
        await create_player(telegram_id, nome, cpf, pix, telefone, cidade, estado)
        
    except ValueError:
        print("ERRO: Telegram ID deve ser um numero inteiro!")
    except KeyboardInterrupt:
        print("\n\nOperacao cancelada pelo usuario.")
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Modo não-interativo com argumentos
        if len(sys.argv) < 3:
            print("Uso: python create_player.py <telegram_id> <nome> [cpf] [pix] [telefone] [cidade] [estado]")
            print("\nExemplo:")
            print("  python create_player.py 123456789 'Joao Silva' '123.456.789-00' 'joao@email.com' '(11) 99999-9999' 'Sao Paulo' 'SP'")
            sys.exit(1)
        
        telegram_id = int(sys.argv[1])
        nome = sys.argv[2]
        cpf = sys.argv[3] if len(sys.argv) > 3 else None
        pix = sys.argv[4] if len(sys.argv) > 4 else None
        telefone = sys.argv[5] if len(sys.argv) > 5 else None
        cidade = sys.argv[6] if len(sys.argv) > 6 else None
        estado = sys.argv[7] if len(sys.argv) > 7 else None
        
        asyncio.run(create_player(telegram_id, nome, cpf, pix, telefone, cidade, estado))
    else:
        # Modo interativo
        asyncio.run(interactive_create())

