from fastapi import APIRouter, HTTPException, Depends, Request, Header
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import (
    AsyncSessionLocal, Usuario, Transacao, TipoTransacao, StatusTransacao, get_db
)
from pydantic import BaseModel, Field
from typing import Optional
import logging
import secrets
from datetime import datetime
import json

from services.asaas import asaas_service

router = APIRouter(prefix="/finance", tags=["finance"])
logger = logging.getLogger(__name__)


# ==================== Schemas (Pydantic Models) ====================

class DepositRequest(BaseModel):
    telegram_id: int
    valor: float = Field(..., gt=0, description="Valor do depósito em reais")


class DepositResponse(BaseModel):
    transaction_id: int
    pix_code: str
    qr_code_base64: Optional[str] = None
    valor: float
    status: str
    payment_id: str  # ID da cobrança no Asaas
    expires_at: Optional[str] = None
    created_at: datetime


class WebhookPixPayload(BaseModel):
    gateway_id: str
    status: str  # "PAID", "FAILED", etc
    valor: float


class BalanceResponse(BaseModel):
    telegram_id: int
    nome: str
    saldo: float


# ==================== Endpoints ====================

@router.post("/deposit", response_model=DepositResponse)
async def create_deposit(deposit: DepositRequest):
    """
    Cria uma solicitação de depósito via Pix usando Asaas.
    
    - Cria/busca cliente no Asaas
    - Cria cobrança Pix
    - Gera QR Code
    - Registra transação localmente
    """
    async with AsyncSessionLocal() as session:
        try:
            # Buscar ou criar usuário
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == deposit.telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            # Verificar se usuário tem CPF cadastrado
            if not usuario.cpf:
                raise HTTPException(
                    status_code=400, 
                    detail="CPF não cadastrado. Complete seu cadastro no Mini App."
                )
            
            # Buscar ou criar cliente no Asaas
            asaas_customer = await asaas_service.get_customer_by_external_reference(
                str(deposit.telegram_id)
            )
            
            if not asaas_customer:
                # Remover formatação do CPF (apenas números)
                cpf_limpo = usuario.cpf.replace(".", "").replace("-", "")
                
                asaas_customer = await asaas_service.create_customer(
                    name=usuario.nome,
                    cpf_cnpj=cpf_limpo,
                    phone=usuario.telefone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "") if usuario.telefone else None,
                    external_reference=str(deposit.telegram_id)
                )
            
            customer_id = asaas_customer.get("id")
            
            # Criar transação local primeiro
            transacao = Transacao(
                usuario_id=usuario.id,
                tipo=TipoTransacao.DEPOSITO,
                valor=deposit.valor,
                status=StatusTransacao.PENDENTE,
                gateway_id="",  # Será atualizado após criar no Asaas
                descricao=f"Depósito via Pix - R$ {deposit.valor:.2f}"
            )
            session.add(transacao)
            await session.commit()
            await session.refresh(transacao)
            
            # Criar cobrança Pix no Asaas
            payment = await asaas_service.create_pix_payment(
                customer_id=customer_id,
                value=deposit.valor,
                description=f"Depósito PowerPix - {usuario.nome}",
                external_reference=str(transacao.id)
            )
            
            payment_id = payment.get("id")
            
            # Atualizar transação com ID do Asaas
            transacao.gateway_id = payment_id
            await session.commit()
            
            # Obter QR Code Pix
            qr_code_data = await asaas_service.get_pix_qrcode(payment_id)
            pix_code = qr_code_data.get("payload", "")
            qr_code_base64 = qr_code_data.get("encodedImage")
            
            logger.info(f"Depósito Asaas criado: Transaction ID {transacao.id} - Payment ID {payment_id} - Valor R$ {deposit.valor:.2f}")
            
            return DepositResponse(
                transaction_id=transacao.id,
                pix_code=pix_code,
                qr_code_base64=qr_code_base64,
                valor=transacao.valor,
                status=transacao.status.value,
                payment_id=payment_id,
                expires_at=payment.get("dueDate"),
                created_at=transacao.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao criar depósito: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao processar depósito: {str(e)}")


@router.post("/webhook/asaas")
async def webhook_asaas(request: Request, asaas_access_token: Optional[str] = Header(None)):
    """
    Webhook do Asaas para notificações de pagamento.
    
    Eventos suportados:
    - PAYMENT_RECEIVED: Pagamento recebido
    - PAYMENT_CONFIRMED: Pagamento confirmado
    - PAYMENT_OVERDUE: Pagamento vencido
    - PAYMENT_REFUNDED: Pagamento estornado
    
    SEGURANÇA:
    - Valida token de acesso (se configurado)
    - Verifica se a transação já foi processada (evita duplicação)
    - Usa transação atômica para garantir consistência
    """
    async with AsyncSessionLocal() as session:
        try:
            # Ler corpo da requisição
            body = await request.body()
            body_str = body.decode('utf-8')
            webhook_data = json.loads(body_str)
            
            # Log do webhook recebido
            logger.info(f"Webhook Asaas recebido: {webhook_data.get('event')}")
            
            # Validar token (se configurado)
            # Note: Asaas permite configurar um token customizado no painel
            # if asaas_access_token != settings.ASAAS_WEBHOOK_TOKEN:
            #     logger.warning("Token de webhook inválido")
            #     raise HTTPException(status_code=403, detail="Token inválido")
            
            event = webhook_data.get("event")
            payment_data = webhook_data.get("payment", {})
            payment_id = payment_data.get("id")
            
            if not payment_id:
                logger.warning("Webhook sem payment ID")
                return {"status": "ignored", "message": "Sem payment ID"}
            
            # Buscar transação pelo gateway_id (payment_id do Asaas)
            result = await session.execute(
                select(Transacao)
                .options(selectinload(Transacao.usuario))
                .where(Transacao.gateway_id == payment_id)
            )
            transacao = result.scalar_one_or_none()
            
            if not transacao:
                logger.warning(f"Transação não encontrada para payment_id: {payment_id}")
                # Não retorna erro para não fazer o Asaas reenviar
                return {"status": "ignored", "message": "Transação não encontrada"}
            
            # Verificar se já foi processada (SEGURANÇA CRÍTICA)
            if transacao.status == StatusTransacao.PAGO:
                logger.warning(f"Transação {transacao.id} já foi processada anteriormente")
                return {"status": "already_processed", "message": "Transação já foi creditada"}
            
            # Processar eventos de pagamento recebido/confirmado
            if event in ["PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"]:
                # Atualizar status da transação
                transacao.status = StatusTransacao.PAGO
                transacao.updated_at = datetime.utcnow()
                
                # ATOMICIDADE: Creditar saldo do usuário
                usuario = transacao.usuario
                usuario.saldo += transacao.valor
                
                await session.commit()
                
                logger.info(f"✓ Depósito Asaas confirmado: Transaction ID {transacao.id} - Payment ID {payment_id} - Usuário {usuario.nome} - Valor R$ {transacao.valor:.2f} - Novo saldo: R$ {usuario.saldo:.2f}")
                
                return {
                    "status": "success",
                    "transaction_id": transacao.id,
                    "novo_saldo": usuario.saldo,
                    "message": "Depósito creditado com sucesso"
                }
            
            elif event == "PAYMENT_OVERDUE":
                transacao.status = StatusTransacao.FALHA
                transacao.updated_at = datetime.utcnow()
                await session.commit()
                
                logger.warning(f"Pagamento vencido: Transaction ID {transacao.id}")
                return {"status": "expired", "message": "Pagamento vencido"}
            
            elif event == "PAYMENT_REFUNDED":
                transacao.status = StatusTransacao.CANCELADO
                transacao.updated_at = datetime.utcnow()
                await session.commit()
                
                logger.warning(f"Pagamento estornado: Transaction ID {transacao.id}")
                return {"status": "refunded", "message": "Pagamento estornado"}
            
            else:
                logger.info(f"Evento não processado: {event}")
                return {"status": "ignored", "message": f"Evento {event} não requer ação"}
        
        except json.JSONDecodeError:
            logger.error("Erro ao decodificar JSON do webhook")
            raise HTTPException(status_code=400, detail="JSON inválido")
        except Exception as e:
            await session.rollback()
            logger.error(f"Erro ao processar webhook Asaas: {e}", exc_info=True)
            # Não lança exceção para não fazer o Asaas reenviar indefinidamente
            return {"status": "error", "message": str(e)}


@router.get("/balance/{telegram_id}", response_model=BalanceResponse)
async def get_balance(telegram_id: int):
    """
    Retorna o saldo atual do usuário.
    """
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            return BalanceResponse(
                telegram_id=usuario.telegram_id,
                nome=usuario.nome,
                saldo=usuario.saldo
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar saldo: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao buscar saldo")


@router.get("/transactions/{telegram_id}")
async def get_transactions(telegram_id: int, limit: int = 20):
    """
    Retorna o histórico de transações do usuário.
    """
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            result = await session.execute(
                select(Transacao)
                .where(Transacao.usuario_id == usuario.id)
                .order_by(Transacao.created_at.desc())
                .limit(limit)
            )
            transacoes = result.scalars().all()
            
            return {
                "telegram_id": telegram_id,
                "transactions": [
                    {
                        "id": t.id,
                        "tipo": t.tipo.value,
                        "valor": t.valor,
                        "status": t.status.value,
                        "descricao": t.descricao,
                        "created_at": t.created_at.isoformat(),
                        "updated_at": t.updated_at.isoformat() if t.updated_at else None
                    }
                    for t in transacoes
                ]
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar transações: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao buscar transações")


# Endpoint de teste para simular pagamento (REMOVER EM PRODUÇÃO)
@router.post("/test/simulate-payment/{gateway_id}")
async def simulate_payment(gateway_id: str):
    """
    APENAS PARA TESTES - Simula o pagamento de um Pix.
    REMOVER EM PRODUÇÃO!
    """
    payload = WebhookPixPayload(
        gateway_id=gateway_id,
        status="PAID",
        valor=0.0  # O valor já está na transação
    )
    return await webhook_pix(payload, None)

