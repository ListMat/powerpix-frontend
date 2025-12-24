from fastapi import APIRouter, HTTPException
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from database import (
    AsyncSessionLocal, Usuario, Aposta, Sorteio, StatusSorteio, Concurso, Transacao, TipoTransacao
)
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import logging
from pydantic import BaseModel as PydanticBaseModel

router = APIRouter(prefix="/api/player", tags=["player"])
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

class CheckRegistrationRequest(BaseModel):
    telegram_id: int


class LoginRequest(BaseModel):
    cpf: str
    telefone: str


class LoginResponse(BaseModel):
    success: bool
    telegram_id: int
    nome: str
    cadastro_completo: bool
    message: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login do usuário usando CPF e telefone.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Limpar formatação
            cpf_limpo = request.cpf.replace(".", "").replace("-", "").strip()
            telefone_limpo = request.telefone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "").strip()
            
            # Buscar usuário por CPF e telefone
            result = await session.execute(
                select(Usuario).where(
                    Usuario.cpf == cpf_limpo,
                    Usuario.telefone == telefone_limpo
                )
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                return LoginResponse(
                    success=False,
                    telegram_id=0,
                    nome="",
                    cadastro_completo=False,
                    message="CPF ou telefone inválidos"
                )
            
            # Verificar se conta está arquivada
            if usuario.is_archived:
                return LoginResponse(
                    success=False,
                    telegram_id=0,
                    nome=usuario.nome or "",
                    cadastro_completo=usuario.cadastro_completo or False,
                    message="Sua conta foi arquivada. Entre em contato com o administrador para reativá-la."
                )
            
            # Verificar se tem telegram_id (está vinculado ao Telegram)
            if not usuario.telegram_id:
                return LoginResponse(
                    success=False,
                    telegram_id=0,
                    nome=usuario.nome or "",
                    cadastro_completo=usuario.cadastro_completo or False,
                    message="Usuário não vinculado ao Telegram. Acesse pelo bot primeiro."
                )
            
            return LoginResponse(
                success=True,
                telegram_id=usuario.telegram_id,
                nome=usuario.nome or "",
                cadastro_completo=usuario.cadastro_completo or False,
                message="Login realizado com sucesso"
            )
            
        except Exception as e:
            logger.error(f"Erro ao fazer login: {e}", exc_info=True)
            return LoginResponse(
                success=False,
                telegram_id=0,
                nome="",
                cadastro_completo=False,
                message="Erro ao processar login"
            )


@router.post("/check-registration")
async def check_registration(request: CheckRegistrationRequest):
    """
    Verifica se o usuário está cadastrado e com dados completos.
    """
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == request.telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                return {
                    "cadastro_completo": False,
                    "usuario_existe": False,
                    "mensagem": "Usuário não encontrado. Complete seu cadastro."
                }
            
            # Verificar se cadastro está completo
            cadastro_completo = (
                usuario.cadastro_completo and
                usuario.nome and
                usuario.cpf and
                usuario.pix and
                usuario.telefone
            )
            
            return {
                "cadastro_completo": cadastro_completo,
                "usuario_existe": True,
                "nome": usuario.nome,
                "tem_cpf": bool(usuario.cpf),
                "tem_pix": bool(usuario.pix),
                "tem_telefone": bool(usuario.telefone),
                "mensagem": "Cadastro completo" if cadastro_completo else "Cadastro incompleto"
            }
        except Exception as e:
            logger.error(f"Erro ao verificar cadastro: {e}", exc_info=True)
            return {
                "cadastro_completo": False,
                "usuario_existe": False,
                "mensagem": "Erro ao verificar cadastro"
            }


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


@router.get("/history/bets/{telegram_id}")
async def get_bet_history(telegram_id: int, limit: int = 20):
    """
    Retorna histórico de apostas do jogador (últimas 20 por padrão).
    """
    async with AsyncSessionLocal() as session:
        try:
            # Buscar usuário
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                return {"apostas": []}
            
            # Buscar apostas com sorteio/concurso
            result = await session.execute(
                select(Aposta)
                .options(selectinload(Aposta.sorteio), selectinload(Aposta.concurso))
                .where(Aposta.usuario_id == usuario.id)
                .order_by(desc(Aposta.data_aposta))
                .limit(limit)
            )
            apostas = result.scalars().all()
            
            apostas_list = []
            for aposta in apostas:
                # Determinar status
                if aposta.is_winner:
                    status = "GANHOU"
                    status_color = "green"
                elif aposta.sorteio and aposta.sorteio.status == StatusSorteio.ENCERRADO:
                    status = "PERDEU"
                    status_color = "red"
                elif aposta.concurso and aposta.concurso.is_drawn:
                    status = "PERDEU"
                    status_color = "red"
                else:
                    status = "AGUARDANDO"
                    status_color = "yellow"
                
                # Nome do concurso/sorteio
                concurso_nome = ""
                if aposta.concurso:
                    concurso_nome = aposta.concurso.titulo
                elif aposta.sorteio:
                    concurso_nome = f"Sorteio #{aposta.sorteio.id}"
                else:
                    concurso_nome = "Sorteio Antigo"
                
                apostas_list.append({
                    "id": aposta.id,
                    "numeros_brancos": aposta.numeros_brancos,
                    "numeros_vermelhos": aposta.numeros_vermelhos,
                    "valor_pago": aposta.valor_pago,
                    "data_aposta": aposta.data_aposta.strftime("%d/%m/%Y %H:%M") if aposta.data_aposta else "",
                    "status": status,
                    "status_color": status_color,
                    "acertos": aposta.acertos or 0,
                    "valor_premio": aposta.valor_premio or 0.0,
                    "concurso_nome": concurso_nome
                })
            
            return {"apostas": apostas_list}
        
        except Exception as e:
            logger.error(f"Erro ao buscar histórico de apostas: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao buscar histórico")


@router.get("/history/transactions/{telegram_id}")
async def get_transaction_history(telegram_id: int, limit: int = 20):
    """
    Retorna histórico de transações (depósitos, saques, apostas, prêmios).
    """
    async with AsyncSessionLocal() as session:
        try:
            # Buscar usuário
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                return {"transacoes": []}
            
            # Buscar transações
            result = await session.execute(
                select(Transacao)
                .where(Transacao.usuario_id == usuario.id)
                .order_by(desc(Transacao.data_criacao))
                .limit(limit)
            )
            transacoes = result.scalars().all()
            
            transacoes_list = []
            for t in transacoes:
                # Determinar ícone e cor
                if t.tipo == TipoTransacao.DEPOSITO:
                    icone = "💰"
                    cor = "green"
                    descricao = "Depósito PIX"
                elif t.tipo == TipoTransacao.APOSTA:
                    icone = "🎮"
                    cor = "blue"
                    descricao = "Aposta realizada"
                elif t.tipo == TipoTransacao.PREMIO:
                    icone = "🏆"
                    cor = "gold"
                    descricao = "Prêmio recebido"
                elif t.tipo == TipoTransacao.SAQUE:
                    icone = "💸"
                    cor = "orange"
                    descricao = "Saque PIX"
                else:
                    icone = "📝"
                    cor = "gray"
                    descricao = t.descricao or "Transação"
                
                transacoes_list.append({
                    "id": t.id,
                    "tipo": t.tipo.value if hasattr(t.tipo, 'value') else str(t.tipo),
                    "valor": t.valor,
                    "descricao": descricao,
                    "icone": icone,
                    "cor": cor,
                    "data": t.data_criacao.strftime("%d/%m/%Y %H:%M") if t.data_criacao else "",
                    "status": t.status
                })
            
            return {"transacoes": transacoes_list}
        
        except Exception as e:
            logger.error(f"Erro ao buscar histórico de transações: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao buscar histórico")


@router.get("/config/bet-price")
async def get_bet_price():
    """
    Retorna o preço atual da aposta.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Buscar concurso ativo
            from database import StatusConcurso
            result = await session.execute(
                select(Concurso)
                .where(
                    and_(
                        Concurso.status == StatusConcurso.ATIVO,
                        Concurso.is_active == True
                    )
                )
                .order_by(desc(Concurso.data_criacao))
                .limit(1)
            )
            concurso = result.scalar_one_or_none()
            
            if concurso:
                return {
                    "preco": concurso.preco_cota,
                    "concurso_id": concurso.id,
                    "concurso_nome": concurso.titulo or f"Concurso #{concurso.id}",
                    "premio_total": concurso.premio_total or 0.0,
                    "data_sorteio_prevista": concurso.data_sorteio_prevista.isoformat() if concurso.data_sorteio_prevista else None
                }
            
            # Fallback: preço padrão
            return {
                "preco": 5.0,
                "concurso_id": None,
                "concurso_nome": "Aguardando novo concurso",
                "premio_total": 0.0,
                "data_sorteio_prevista": None
            }
        
        except Exception as e:
            logger.error(f"Erro ao buscar preço da aposta: {e}", exc_info=True)
            return {
                "preco": 5.0,
                "concurso_id": None,
                "concurso_nome": "Aguardando novo concurso",
                "premio_total": 0.0,
                "data_sorteio_prevista": None
            }


# ==================== PERFIL DO USUÁRIO ====================

class ProfileResponse(BaseModel):
    telegram_id: int
    nome: str
    cpf: Optional[str]
    pix: Optional[str]
    telefone: Optional[str]
    cidade: Optional[str]
    estado: Optional[str]
    saldo: float
    data_cadastro: str
    cadastro_completo: bool
    is_archived: bool


@router.get("/profile/{telegram_id}", response_model=ProfileResponse)
async def get_profile(telegram_id: int):
    """
    Retorna os dados do perfil do usuário.
    """
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                logger.warning(f"Usuário não encontrado: telegram_id={telegram_id}")
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            # Validar dados antes de retornar
            if not usuario.nome:
                logger.warning(f"Usuário sem nome: telegram_id={telegram_id}")
            
            return ProfileResponse(
                telegram_id=usuario.telegram_id,
                nome=usuario.nome or "",
                cpf=usuario.cpf,
                pix=usuario.pix,
                telefone=usuario.telefone,
                cidade=usuario.cidade,
                estado=usuario.estado,
                saldo=float(usuario.saldo) if usuario.saldo is not None else 0.0,
                data_cadastro=usuario.data_cadastro.isoformat() if usuario.data_cadastro else "",
                cadastro_completo=bool(usuario.cadastro_completo) if usuario.cadastro_completo is not None else False,
                is_archived=bool(usuario.is_archived) if usuario.is_archived is not None else False
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar perfil (telegram_id={telegram_id}): {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao buscar perfil: {str(e)}")


class ArchiveAccountRequest(BaseModel):
    telegram_id: int


@router.post("/profile/archive")
async def archive_account(request: ArchiveAccountRequest):
    """
    Arquivar conta do usuário (soft delete).
    A conta não será deletada, apenas arquivada.
    """
    async with AsyncSessionLocal() as session:
        try:
            from datetime import datetime
            
            result = await session.execute(
                select(Usuario).where(Usuario.telegram_id == request.telegram_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            if usuario.is_archived:
                return {"message": "Conta já está arquivada", "success": True}
            
            usuario.is_archived = True
            usuario.data_arquivamento = datetime.utcnow()
            
            await session.commit()
            
            return {
                "message": "Conta arquivada com sucesso. O administrador pode reativá-la a qualquer momento.",
                "success": True
            }
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Erro ao arquivar conta: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao arquivar conta")

