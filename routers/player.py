from fastapi import APIRouter, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from database import (
    AsyncSessionLocal, Usuario, Aposta, Sorteio, StatusSorteio
)
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import logging

router = APIRouter(prefix="/player", tags=["player"])
logger = logging.getLogger(__name__)


# ==================== Schemas ====================

class BetNumber(BaseModel):
    brancos: List[int]
    vermelhos: List[int]


class BetResponse(BaseModel):
    id: int
    numeros_brancos: List[int]
    numeros_vermelhos: List[int]
    valor_pago: float
    data_aposta: str
    sorteio_id: Optional[int]
    sorteio_status: Optional[str]
    is_winner: bool
    acertos: int
    valor_premio: float
    status_display: str  # "ATIVO", "GANHOU", "PERDEU", "AGUARDANDO"


class DrawResultResponse(BaseModel):
    sorteio_id: int
    data_sorteio: str
    status: str
    numeros_sorteados_brancos: Optional[List[int]]
    numeros_sorteados_vermelhos: Optional[List[int]]
    apostas_usuario: List[BetResponse]


# ==================== Endpoints ====================

@router.get("/my-bets/{telegram_id}")
async def get_my_bets(telegram_id: int, limit: int = 50):
    """
    Retorna todas as apostas do usuário, separadas por status:
    - jogos_ativos: Apostas em sorteios ainda ABERTOS
    - historico: Apostas em sorteios FECHADOS (já sorteados)
    """
    async with AsyncSessionLocal() as session:
        try:
            # Buscar usuário
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            # Buscar todas as apostas do usuário com os sorteios relacionados
            result = await session.execute(
                select(Aposta)
                .options(selectinload(Aposta.sorteio))
                .where(Aposta.usuario_id == usuario.id)
                .order_by(Aposta.data_aposta.desc())
                .limit(limit)
            )
            apostas = result.scalars().all()
            
            jogos_ativos = []
            historico = []
            
            for aposta in apostas:
                # Determinar status de exibição
                if aposta.sorteio:
                    if aposta.sorteio.status == StatusSorteio.ABERTO:
                        status_display = "AGUARDANDO"
                    elif aposta.is_winner:
                        status_display = "GANHOU"
                    else:
                        status_display = "PERDEU"
                else:
                    status_display = "AGUARDANDO"
                
                bet_data = BetResponse(
                    id=aposta.id,
                    numeros_brancos=json.loads(aposta.numeros_brancos),
                    numeros_vermelhos=json.loads(aposta.numeros_vermelhos),
                    valor_pago=aposta.valor_pago,
                    data_aposta=aposta.data_aposta.isoformat(),
                    sorteio_id=aposta.sorteio_id,
                    sorteio_status=aposta.sorteio.status.value if aposta.sorteio else None,
                    is_winner=aposta.is_winner,
                    acertos=aposta.acertos,
                    valor_premio=aposta.valor_premio,
                    status_display=status_display
                )
                
                # Separar entre ativos e histórico
                if aposta.sorteio and aposta.sorteio.status == StatusSorteio.ABERTO:
                    jogos_ativos.append(bet_data)
                else:
                    historico.append(bet_data)
            
            return {
                "telegram_id": telegram_id,
                "nome": usuario.nome,
                "total_apostas": len(apostas),
                "jogos_ativos": jogos_ativos,
                "historico": historico
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar apostas: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao buscar apostas")


@router.get("/results/{draw_id}", response_model=DrawResultResponse)
async def get_draw_results(draw_id: int, telegram_id: int):
    """
    Mostra os resultados de um sorteio específico e destaca os acertos do usuário.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Buscar usuário
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            # Buscar sorteio
            result = await session.execute(
                select(Sorteio).where(Sorteio.id == draw_id)
            )
            sorteio = result.scalar_one_or_none()
            
            if not sorteio:
                raise HTTPException(status_code=404, detail="Sorteio não encontrado")
            
            # Parse números sorteados
            numeros_brancos_sorteados = None
            numeros_vermelhos_sorteados = None
            
            if sorteio.numeros_sorteados:
                try:
                    numeros = json.loads(sorteio.numeros_sorteados)
                    numeros_brancos_sorteados = numeros.get("brancos", [])
                    numeros_vermelhos_sorteados = numeros.get("vermelhos", [])
                except:
                    pass
            
            # Buscar apostas do usuário neste sorteio
            result = await session.execute(
                select(Aposta)
                .where(and_(
                    Aposta.usuario_id == usuario.id,
                    Aposta.sorteio_id == draw_id
                ))
                .order_by(Aposta.data_aposta.desc())
            )
            apostas = result.scalars().all()
            
            apostas_response = []
            for aposta in apostas:
                status_display = "GANHOU" if aposta.is_winner else "PERDEU"
                if sorteio.status == StatusSorteio.ABERTO:
                    status_display = "AGUARDANDO"
                
                apostas_response.append(BetResponse(
                    id=aposta.id,
                    numeros_brancos=json.loads(aposta.numeros_brancos),
                    numeros_vermelhos=json.loads(aposta.numeros_vermelhos),
                    valor_pago=aposta.valor_pago,
                    data_aposta=aposta.data_aposta.isoformat(),
                    sorteio_id=aposta.sorteio_id,
                    sorteio_status=sorteio.status.value,
                    is_winner=aposta.is_winner,
                    acertos=aposta.acertos,
                    valor_premio=aposta.valor_premio,
                    status_display=status_display
                ))
            
            return DrawResultResponse(
                sorteio_id=sorteio.id,
                data_sorteio=sorteio.data.isoformat(),
                status=sorteio.status.value,
                numeros_sorteados_brancos=numeros_brancos_sorteados,
                numeros_sorteados_vermelhos=numeros_vermelhos_sorteados,
                apostas_usuario=apostas_response
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar resultados: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao buscar resultados")


@router.get("/stats/{telegram_id}")
async def get_player_stats(telegram_id: int):
    """
    Retorna estatísticas gerais do jogador.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Buscar usuário
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            # Buscar todas as apostas
            result = await session.execute(
                select(Aposta)
                .options(selectinload(Aposta.sorteio))
                .where(Aposta.usuario_id == usuario.id)
            )
            apostas = result.scalars().all()
            
            # Calcular estatísticas
            total_apostas = len(apostas)
            total_gasto = sum(a.valor_pago for a in apostas)
            total_ganho = sum(a.valor_premio for a in apostas if a.is_winner)
            total_vitorias = sum(1 for a in apostas if a.is_winner)
            
            # Apostas ativas (sorteios abertos)
            apostas_ativas = sum(
                1 for a in apostas 
                if a.sorteio and a.sorteio.status == StatusSorteio.ABERTO
            )
            
            return {
                "telegram_id": telegram_id,
                "nome": usuario.nome,
                "saldo_atual": usuario.saldo,
                "total_apostas": total_apostas,
                "total_gasto": total_gasto,
                "total_ganho": total_ganho,
                "lucro_liquido": total_ganho - total_gasto,
                "total_vitorias": total_vitorias,
                "taxa_vitoria": (total_vitorias / total_apostas * 100) if total_apostas > 0 else 0,
                "apostas_ativas": apostas_ativas
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao buscar estatísticas")

