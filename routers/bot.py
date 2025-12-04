from fastapi import APIRouter, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import json
import logging
from database import (
    AsyncSessionLocal, Usuario, Sorteio, Aposta, StatusSorteio, SystemConfig, 
    Transacao, TipoTransacao, StatusTransacao
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter()

# Bot e Dispatcher
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handler do comando /start"""
    webapp_url = f"{settings.WEBHOOK_URL}/webapp" if settings.WEBHOOK_URL else "https://seu-dominio.com/webapp"
    
    # Buscar ou criar usuário
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Usuario).where(Usuario.telegram_id == message.from_user.id)
        )
        usuario = result.scalar_one_or_none()
        
        if not usuario:
            nome = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            if not nome:
                nome = message.from_user.username or f"User_{message.from_user.id}"
            
            usuario = Usuario(
                telegram_id=message.from_user.id,
                nome=nome
            )
            session.add(usuario)
            await session.commit()
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎲 Fazer Aposta",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Ver Saldo",
                    callback_data="saldo"
                ),
                InlineKeyboardButton(
                    text="📊 Meus Jogos",
                    callback_data="meus_jogos"
                )
            ]
        ]
    )
    
    await message.answer(
        "🎉 Bem-vindo ao PowerPix!\n\n"
        "💰 Sistema de carteira digital\n"
        "🎯 Escolha seus números da sorte\n"
        "🏆 Concorra a prêmios incríveis\n\n"
        "Use /saldo para ver seu saldo\n"
        "Use /depositar para adicionar créditos",
        reply_markup=keyboard
    )


@dp.message(Command("saldo"))
async def cmd_saldo(message: types.Message):
    """Mostra o saldo do usuário"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Usuario).where(Usuario.telegram_id == message.from_user.id)
        )
        usuario = result.scalar_one_or_none()
        
        if not usuario:
            await message.answer("❌ Usuário não encontrado. Use /start primeiro.")
            return
        
        await message.answer(
            f"💰 Seu Saldo\n\n"
            f"Disponível: R$ {usuario.saldo:.2f}\n\n"
            f"💳 Use /depositar para adicionar créditos\n"
            f"🎲 Use /apostar para fazer uma aposta"
        )


@dp.message(Command("depositar"))
async def cmd_depositar(message: types.Message):
    """Inicia o processo de depósito"""
    await message.answer(
        "💳 Depósito via Pix\n\n"
        "Para depositar, acesse a API:\n"
        "POST /finance/deposit\n\n"
        "Ou use o painel web para gerar um código Pix.\n\n"
        "Em breve teremos o processo integrado diretamente no bot!"
    )


@dp.message(Command("meusJogos"))
async def cmd_meus_jogos(message: types.Message):
    """Mostra as apostas do usuário"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Usuario).where(Usuario.telegram_id == message.from_user.id)
        )
        usuario = result.scalar_one_or_none()
        
        if not usuario:
            await message.answer("❌ Usuário não encontrado. Use /start primeiro.")
            return
        
        # Buscar apostas recentes
        result = await session.execute(
            select(Aposta)
            .options(selectinload(Aposta.sorteio))
            .where(Aposta.usuario_id == usuario.id)
            .order_by(Aposta.data_aposta.desc())
            .limit(10)
        )
        apostas = result.scalars().all()
        
        if not apostas:
            await message.answer(
                "📊 Você ainda não fez nenhuma aposta.\n\n"
                "🎲 Use o botão abaixo para fazer sua primeira aposta!"
            )
            return
        
        mensagem = "📊 Suas Últimas Apostas\n\n"
        
        for aposta in apostas:
            brancos = json.loads(aposta.numeros_brancos)
            vermelhos = json.loads(aposta.numeros_vermelhos)
            
            if aposta.sorteio:
                if aposta.sorteio.status == StatusSorteio.ABERTO:
                    status = "🟡 Aguardando sorteio"
                elif aposta.is_winner:
                    status = f"🟢 Ganhou R$ {aposta.valor_premio:.2f}"
                else:
                    status = "🔴 Não ganhou"
            else:
                status = "🟡 Aguardando"
            
            mensagem += (
                f"#{aposta.id} - {status}\n"
                f"⚪ {len(brancos)} brancos | 🔴 {len(vermelhos)} vermelhos\n"
                f"💰 R$ {aposta.valor_pago:.2f}\n"
                f"📅 {aposta.data_aposta.strftime('%d/%m/%Y %H:%M')}\n\n"
            )
        
        await message.answer(mensagem)


@dp.message(lambda message: message.web_app_data is not None)
async def handle_web_app_data(message: types.Message):
    """Handler para receber dados do Mini App"""
    try:
        # Parsear JSON recebido
        data_str = message.web_app_data.data
        data = json.loads(data_str)
        
        # Validar estrutura
        if data.get("action") != "aposta_realizada":
            await message.answer("❌ Erro: Ação inválida.")
            return
        
        white_numbers = data.get("white", [])
        red_numbers = data.get("red", [])
        
        if not white_numbers or not red_numbers:
            await message.answer("❌ Erro: Números não fornecidos corretamente.")
            return
        
        async with AsyncSessionLocal() as session:
            # Buscar sorteio atual (ABERTO)
            result = await session.execute(
                select(Sorteio).where(Sorteio.status == StatusSorteio.ABERTO)
            )
            sorteio_atual = result.scalar_one_or_none()
            
            if not sorteio_atual:
                await message.answer(
                    "❌ Não há sorteio aberto no momento. "
                    "Aguarde a abertura de um novo sorteio."
                )
                return
            
            # Buscar ou criar usuário
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == message.from_user.id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                nome = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
                if not nome:
                    nome = message.from_user.username or f"User_{message.from_user.id}"
                
                usuario = Usuario(
                    telegram_id=message.from_user.id,
                    nome=nome
                )
                session.add(usuario)
                await session.flush()
            
            # Calcular preço da aposta
            valor_aposta = data.get("valor_pago")
            if not valor_aposta:
                # Se não veio do frontend, buscar do sistema
                result = await session.execute(select(SystemConfig).limit(1))
                config = result.scalar_one_or_none()
                
                if config:
                    # Aplicar lógica de preço dinâmico
                    if config.is_promo_active:
                        if config.override_price > 0:
                            valor_aposta = config.override_price
                        elif config.current_discount_percent > 0:
                            discount_factor = 1 - (config.current_discount_percent / 100)
                            valor_aposta = config.default_pack_price * discount_factor
                        else:
                            valor_aposta = config.default_pack_price
                    else:
                        valor_aposta = config.default_pack_price
                else:
                    # Fallback para valor padrão
                    valor_aposta = settings.VALOR_APOSTA
            else:
                valor_aposta = float(valor_aposta)
            
            # VERIFICAR SALDO DO USUÁRIO (NOVA LÓGICA)
            if usuario.saldo < valor_aposta:
                saldo_faltante = valor_aposta - usuario.saldo
                await message.answer(
                    f"❌ Saldo insuficiente!\n\n"
                    f"💰 Seu saldo: R$ {usuario.saldo:.2f}\n"
                    f"💵 Valor da aposta: R$ {valor_aposta:.2f}\n"
                    f"📉 Falta: R$ {saldo_faltante:.2f}\n\n"
                    f"💳 Use /depositar para adicionar saldo à sua carteira."
                )
                return
            
            # DEDUZIR DO SALDO (ATOMICIDADE)
            usuario.saldo -= valor_aposta
            
            # Registrar transação de aposta
            transacao = Transacao(
                usuario_id=usuario.id,
                tipo=TipoTransacao.APOSTA,
                valor=valor_aposta,
                status=StatusTransacao.PAGO,
                descricao=f"Aposta no sorteio #{sorteio_atual.id}"
            )
            session.add(transacao)
            
            # Criar aposta
            aposta = Aposta(
                usuario_id=usuario.id,
                sorteio_id=sorteio_atual.id,
                numeros_brancos=json.dumps(white_numbers),
                numeros_vermelhos=json.dumps(red_numbers),
                valor_pago=valor_aposta
            )
            session.add(aposta)
            await session.commit()
            
            total_numeros = len(white_numbers) + len(red_numbers)
            await message.answer(
                f"✅ Aposta registrada com sucesso!\n\n"
                f"📊 Você selecionou {total_numeros} números:\n"
                f"⚪ Brancos: {len(white_numbers)}\n"
                f"🔴 Powerballs: {len(red_numbers)}\n\n"
                f"💰 Valor: R$ {valor_aposta:.2f}\n"
                f"💵 Saldo restante: R$ {usuario.saldo:.2f}\n\n"
                f"🎯 Boa sorte no sorteio!"
            )
            
    except json.JSONDecodeError:
        await message.answer("❌ Erro ao processar os dados recebidos.")
        logger.error("Erro ao decodificar JSON do web_app_data")
    except Exception as e:
        await message.answer("❌ Ocorreu um erro ao processar sua aposta. Tente novamente.")
        logger.error(f"Erro ao processar aposta: {e}", exc_info=True)


@router.post("/webhook/{token}")
async def webhook_handler(token: str, request: Request):
    """Endpoint para receber updates do Telegram"""
    if token != settings.BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.feed_update(bot=bot, update=update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Erro no webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")

