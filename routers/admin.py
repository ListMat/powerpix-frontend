from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import csv
from io import StringIO
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime
import json
from jose import JWTError, jwt
import bcrypt
from database import (
    AsyncSessionLocal, Usuario, Sorteio, Aposta, Admin, StatusSorteio, SystemConfig, 
    Concurso, Promocao, StatusConcurso, TipoPromocao, get_db
)
from schemas import DrawNumbersSchema
from pydantic import ValidationError
from config import get_settings
from typing import Optional
from template_config import templates  # Importar templates compartilhado

settings = get_settings()

router = APIRouter(prefix="/admin", tags=["admin"])

# Configurações JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(data: dict):
    """Criar JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow().timestamp() + (ACCESS_TOKEN_EXPIRE_HOURS * 3600)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verificar e decodificar JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_admin(request: Request, db: AsyncSession = Depends(get_db)):
    """Dependency para verificar autenticação admin"""
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(Admin).where(Admin.username == username))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    return admin


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Processar login"""
    result = await db.execute(select(Admin).where(Admin.username == username))
    admin = result.scalar_one_or_none()
    
    if not admin or not bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuário ou senha inválidos"}
        )
    
    # Criar token JWT
    access_token = create_access_token(data={"sub": admin.username})
    
    # Criar resposta com redirect
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        secure=False,  # True em produção com HTTPS
        samesite="lax"
    )
    return response


@router.post("/logout")
async def logout():
    """Logout"""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Dashboard principal"""
    # Buscar concurso ativo (prioridade) ou sorteio (compatibilidade)
    result = await db.execute(
        select(Concurso).where(
            Concurso.is_active == True,
            Concurso.status == StatusConcurso.ATIVO,
            Concurso.is_drawn == False
        ).order_by(Concurso.data_criacao.desc())
    )
    concurso_atual = result.scalar_one_or_none()
    
    # Fallback para Sorteio (compatibilidade)
    result = await db.execute(
        select(Sorteio).where(Sorteio.status == StatusSorteio.ABERTO)
    )
    sorteio_atual = result.scalar_one_or_none()
    
    # Calcular arrecadação
    arrecadacao = 0.0
    lucro_casa = 0.0
    fundo_premios = 0.0
    meta_arrecadacao = 3000.0
    taxa_inicial = 0.3
    taxa_pos_meta = 0.9
    
    if concurso_atual:
        # Somar valor_pago de todas as apostas do concurso
        result = await db.execute(
            select(func.sum(Aposta.valor_pago))
            .where(Aposta.concurso_id == concurso_atual.id)
        )
        arrecadacao = result.scalar() or 0.0
        fundo_premios = concurso_atual.premio_total
        # Para concursos, o lucro é calculado como: arrecadacao - premio_total
        lucro_casa = max(0.0, arrecadacao - fundo_premios)
    elif sorteio_atual:
        # Somar valor_pago de todas as apostas do sorteio
        result = await db.execute(
            select(func.sum(Aposta.valor_pago))
            .where(Aposta.sorteio_id == sorteio_atual.id)
        )
        arrecadacao = result.scalar() or 0.0
        
        meta_arrecadacao = sorteio_atual.meta_arrecadacao
        taxa_inicial = sorteio_atual.taxa_inicial
        taxa_pos_meta = sorteio_atual.taxa_pos_meta
        
        # Lógica financeira
        if arrecadacao <= meta_arrecadacao:
            lucro_casa = arrecadacao * taxa_inicial
        else:
            lucro_casa = (meta_arrecadacao * taxa_inicial) + ((arrecadacao - meta_arrecadacao) * taxa_pos_meta)
        
        fundo_premios = arrecadacao - lucro_casa
    
    # Buscar últimas apostas (de Concurso ou Sorteio)
    if concurso_atual:
        result = await db.execute(
            select(Aposta)
            .options(selectinload(Aposta.usuario))
            .where(Aposta.concurso_id == concurso_atual.id)
            .order_by(Aposta.data_aposta.desc())
            .limit(20)
        )
    elif sorteio_atual:
        result = await db.execute(
            select(Aposta)
            .options(selectinload(Aposta.usuario))
            .where(Aposta.sorteio_id == sorteio_atual.id)
            .order_by(Aposta.data_aposta.desc())
            .limit(20)
        )
    else:
        # Se não houver concurso nem sorteio, buscar últimas apostas gerais
        result = await db.execute(
            select(Aposta)
            .options(selectinload(Aposta.usuario))
            .order_by(Aposta.data_aposta.desc())
            .limit(20)
        )
    apostas = result.scalars().all()
    
    # Formatar apostas para template
    apostas_formatadas = []
    for aposta in apostas:
        try:
            numeros_brancos = json.loads(aposta.numeros_brancos)
            numeros_vermelhos = json.loads(aposta.numeros_vermelhos)
        except:
            numeros_brancos = []
            numeros_vermelhos = []
        
        apostas_formatadas.append({
            "id": aposta.id,
            "usuario": aposta.usuario.nome if aposta.usuario else "Desconhecido",
            "numeros_brancos": numeros_brancos,
            "numeros_vermelhos": numeros_vermelhos,
            "valor": aposta.valor_pago,
            "data": aposta.data_aposta.strftime("%d/%m/%Y %H:%M") if aposta.data_aposta else ""
        })
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "concurso_atual": concurso_atual,
            "sorteio_atual": sorteio_atual,
            "arrecadacao": arrecadacao,
            "lucro_casa": lucro_casa,
            "fundo_premios": fundo_premios,
            "meta_arrecadacao": meta_arrecadacao,
            "taxa_inicial": taxa_inicial,
            "taxa_pos_meta": taxa_pos_meta,
            "apostas": apostas_formatadas
        }
    )


@router.post("/sorteios/criar")
async def criar_sorteio(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Criar novo sorteio (fecha o anterior se existir)"""
    # Fechar sorteio anterior se existir
    result = await db.execute(
        select(Sorteio).where(Sorteio.status == StatusSorteio.ABERTO)
    )
    sorteio_anterior = result.scalar_one_or_none()
    if sorteio_anterior:
        sorteio_anterior.status = StatusSorteio.FECHADO
        await db.commit()
    
    # Criar novo sorteio
    novo_sorteio = Sorteio(
        status=StatusSorteio.ABERTO,
        meta_arrecadacao=3000.0,
        taxa_inicial=0.3,
        taxa_pos_meta=0.9
    )
    db.add(novo_sorteio)
    await db.commit()
    await db.refresh(novo_sorteio)
    
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.post("/sorteios/encerrar")
async def encerrar_sorteio(
    request: Request,
    numeros_sorteados: str = Form(...),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Encerrar sorteio atual"""
    result = await db.execute(
        select(Sorteio).where(Sorteio.status == StatusSorteio.ABERTO)
    )
    sorteio = result.scalar_one_or_none()
    
    if not sorteio:
        raise HTTPException(status_code=404, detail="Nenhum sorteio aberto encontrado")
    
    # Validar e salvar números sorteados
    # Validar e salvar números sorteados
    try:
        # Validar formato com Pydantic
        # O formulário envia uma string JSON, então primeiro decodificamos
        try:
             numeros_raw = json.loads(numeros_sorteados)
        except json.JSONDecodeError:
             raise ValueError("Formato de números inválido (deve ser JSON)")

        validated_data = DrawNumbersSchema(**numeros_raw)
        
        # Se chegou aqui, está validado. Salvamos o JSON original ou o dump do modelo
        sorteio.numeros_sorteados = validated_data.model_dump_json()

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Erro de validação: {e.errors()}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    sorteio.status = StatusSorteio.FECHADO
    await db.commit()
    
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.get("/apostas")
async def listar_apostas(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """API endpoint para listar apostas (JSON)"""
    result = await db.execute(
        select(Aposta)
        .options(selectinload(Aposta.usuario))
        .order_by(Aposta.data_aposta.desc())
        .limit(50)
    )
    apostas = result.scalars().all()
    
    apostas_json = []
    for aposta in apostas:
        try:
            numeros_brancos = json.loads(aposta.numeros_brancos)
            numeros_vermelhos = json.loads(aposta.numeros_vermelhos)
        except:
            numeros_brancos = []
            numeros_vermelhos = []
        
        apostas_json.append({
            "id": aposta.id,
            "usuario": aposta.usuario.nome if aposta.usuario else "Desconhecido",
            "telegram_id": aposta.usuario.telegram_id if aposta.usuario else None,
            "numeros_brancos": numeros_brancos,
            "numeros_vermelhos": numeros_vermelhos,
            "valor": aposta.valor_pago,
            "data": aposta.data_aposta.isoformat() if aposta.data_aposta else None
        })
    
    return {"apostas": apostas_json}


@router.get("/configs", response_class=HTMLResponse)
async def configs_page(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Página de configuração de preços"""
    # Buscar configuração atual
    result = await db.execute(select(SystemConfig).limit(1))
    config = result.scalar_one_or_none()
    
    if not config:
        # Criar configuração padrão se não existir
        config = SystemConfig(
            default_pack_price=25.00,
            current_discount_percent=0,
            override_price=0.0,
            is_promo_active=False
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
    
    return templates.TemplateResponse(
        "configs.html",
        {
            "request": request,
            "config": config
        }
    )


@router.post("/configs/price")
async def update_price_config(
    request: Request,
    default_pack_price: float = Form(None),
    current_discount_percent: int = Form(None),
    override_price: float = Form(None),
    is_promo_active: bool = Form(False),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Atualizar configuração de preços"""
    # Buscar configuração atual
    result = await db.execute(select(SystemConfig).limit(1))
    config = result.scalar_one_or_none()
    
    if not config:
        # Criar se não existir
        config = SystemConfig()
        db.add(config)
    
    # Atualizar campos (apenas se fornecidos)
    if default_pack_price is not None:
        if default_pack_price < 0:
            return templates.TemplateResponse(
                "configs.html",
                {
                    "request": request,
                    "config": config,
                    "error": "O preço padrão não pode ser negativo"
                },
                status_code=400
            )
        config.default_pack_price = default_pack_price
    
    if current_discount_percent is not None:
        if current_discount_percent < 0 or current_discount_percent > 100:
            return templates.TemplateResponse(
                "configs.html",
                {
                    "request": request,
                    "config": config,
                    "error": "O desconto deve estar entre 0 e 100%"
                },
                status_code=400
            )
        config.current_discount_percent = current_discount_percent
    
    if override_price is not None:
        if override_price < 0:
            return templates.TemplateResponse(
                "configs.html",
                {
                    "request": request,
                    "config": config,
                    "error": "O preço fixo não pode ser negativo"
                },
                status_code=400
            )
        config.override_price = override_price
    
    # is_promo_active vem como string "on" ou None do form
    # Vamos tratar isso corretamente
    form_data = await request.form()
    config.is_promo_active = form_data.get("is_promo_active") == "on"
    
    await db.commit()
    await db.refresh(config)
    
    return templates.TemplateResponse(
        "configs.html",
        {
            "request": request,
            "config": config,
            "success": "Configurações atualizadas com sucesso!"
        }
    )


# ==================== ROTAS DE CONCURSOS ====================

@router.get("/concursos", response_class=HTMLResponse)
async def listar_concursos(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os concursos"""
    result = await db.execute(
        select(Concurso)
        .order_by(Concurso.data_criacao.desc())
    )
    concursos = result.scalars().all()
    
    # Calcular estatísticas para cada concurso
    concursos_com_stats = []
    for concurso in concursos:
        # Total de apostas
        result = await db.execute(
            select(func.count(Aposta.id))
            .where(Aposta.concurso_id == concurso.id)
        )
        total_apostas = result.scalar() or 0
        
        # Total arrecadado
        result = await db.execute(
            select(func.sum(Aposta.valor_pago))
            .where(Aposta.concurso_id == concurso.id)
        )
        total_arrecadado = result.scalar() or 0.0
        
        # Total de ganhadores
        result = await db.execute(
            select(func.count(Aposta.id))
            .where(Aposta.concurso_id == concurso.id, Aposta.is_winner == True)
        )
        total_ganhadores = result.scalar() or 0
        
        concursos_com_stats.append({
            "concurso": concurso,
            "total_apostas": total_apostas,
            "total_arrecadado": total_arrecadado,
            "total_ganhadores": total_ganhadores
        })
    
    return templates.TemplateResponse(
        "contests.html",
        {
            "request": request,
            "concursos": concursos_com_stats
        }
    )


@router.post("/concursos/criar")
async def criar_concurso(
    request: Request,
    titulo: str = Form(...),
    premio_total: float = Form(...),
    preco_cota: float = Form(...),
    data_sorteio_prevista: str = Form(None),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Criar novo concurso"""
    try:
        data_sorteio = None
        if data_sorteio_prevista:
            data_sorteio = datetime.fromisoformat(data_sorteio_prevista.replace('Z', '+00:00'))
        
        novo_concurso = Concurso(
            titulo=titulo,
            premio_total=premio_total,
            preco_cota=preco_cota,
            data_sorteio_prevista=data_sorteio,
            status=StatusConcurso.ATIVO,
            is_active=True
        )
        db.add(novo_concurso)
        await db.commit()
        await db.refresh(novo_concurso)
        
        return RedirectResponse(url="/admin/concursos", status_code=303)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar concurso: {str(e)}")


@router.post("/concursos/{concurso_id}/editar")
async def editar_concurso(
    concurso_id: int,
    request: Request,
    titulo: str = Form(...),
    premio_total: float = Form(...),
    preco_cota: float = Form(...),
    data_sorteio_prevista: str = Form(None),
    is_active: bool = Form(False),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Editar concurso existente"""
    result = await db.execute(
        select(Concurso).where(Concurso.id == concurso_id)
    )
    concurso = result.scalar_one_or_none()
    
    if not concurso:
        raise HTTPException(status_code=404, detail="Concurso não encontrado")
    
    try:
        concurso.titulo = titulo
        concurso.premio_total = premio_total
        concurso.preco_cota = preco_cota
        concurso.is_active = is_active
        
        if data_sorteio_prevista:
            concurso.data_sorteio_prevista = datetime.fromisoformat(data_sorteio_prevista.replace('Z', '+00:00'))
        
        if not is_active:
            concurso.status = StatusConcurso.INATIVO
        elif concurso.is_drawn:
            concurso.status = StatusConcurso.SORTEADO
        else:
            concurso.status = StatusConcurso.ATIVO
        
        await db.commit()
        await db.refresh(concurso)
        
        return RedirectResponse(url="/admin/concursos", status_code=303)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao editar concurso: {str(e)}")


@router.get("/concursos/{concurso_id}", response_class=HTMLResponse)
async def detalhes_concurso(
    concurso_id: int,
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Página de detalhes e relatórios do concurso"""
    result = await db.execute(
        select(Concurso).where(Concurso.id == concurso_id)
    )
    concurso = result.scalar_one_or_none()
    
    if not concurso:
        raise HTTPException(status_code=404, detail="Concurso não encontrado")
    
    # Buscar todas as apostas do concurso
    result = await db.execute(
        select(Aposta)
        .options(selectinload(Aposta.usuario))
        .where(Aposta.concurso_id == concurso_id)
        .order_by(Aposta.data_aposta.desc())
    )
    apostas = result.scalars().all()
    
    # Calcular estatísticas
    total_apostas = len(apostas)
    
    result = await db.execute(
        select(func.sum(Aposta.valor_pago))
        .where(Aposta.concurso_id == concurso_id)
    )
    total_arrecadado = result.scalar() or 0.0
    
    result = await db.execute(
        select(func.count(func.distinct(Aposta.usuario_id)))
        .where(Aposta.concurso_id == concurso_id)
    )
    jogadores_unicos = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Aposta.id))
        .where(Aposta.concurso_id == concurso_id, Aposta.is_winner == True)
    )
    total_ganhadores = result.scalar() or 0
    
    result = await db.execute(
        select(func.sum(Aposta.valor_premio))
        .where(Aposta.concurso_id == concurso_id, Aposta.is_winner == True)
    )
    premio_distribuido = result.scalar() or 0.0
    
    # Processar apostas para exibição
    apostas_formatadas = []
    numeros_sorteados = {"white": [], "powerball": []}
    if concurso.numeros_sorteados:
        try:
            numeros_sorteados = json.loads(concurso.numeros_sorteados)
            # Garantir formato correto
            if not isinstance(numeros_sorteados, dict):
                numeros_sorteados = {"white": numeros_sorteados if isinstance(numeros_sorteados, list) else [], "powerball": []}
        except:
            numeros_sorteados = {"white": [], "powerball": []}
    
    for aposta in apostas:
        try:
            numeros_brancos = json.loads(aposta.numeros_brancos)
            numeros_vermelhos = json.loads(aposta.numeros_vermelhos)
            todos_numeros = numeros_brancos + numeros_vermelhos
        except:
            numeros_brancos = []
            numeros_vermelhos = []
            todos_numeros = []
        
        # Calcular acertos se houver números sorteados
        acertos = aposta.acertos
        if numeros_sorteados and isinstance(numeros_sorteados, dict):
            white_sorted = set(numeros_sorteados.get("white", []))  # 5 números oficiais
            powerball_sorted = numeros_sorteados.get("powerball", [])
            powerball_oficial = powerball_sorted[0] if powerball_sorted else None
            
            acertos_brancos = len(set(numeros_brancos) & white_sorted)
            acertou_powerball = powerball_oficial in numeros_vermelhos if powerball_oficial else False
            acertos = acertos_brancos + (1 if acertou_powerball else 0)
        
        apostas_formatadas.append({
            "id": aposta.id,
            "usuario": aposta.usuario.nome if aposta.usuario else "Desconhecido",
            "telegram_id": aposta.usuario.telegram_id if aposta.usuario else None,
            "numeros_brancos": numeros_brancos,
            "numeros_vermelhos": numeros_vermelhos,
            "valor_pago": aposta.valor_pago,
            "data_aposta": aposta.data_aposta.strftime("%d/%m/%Y %H:%M") if aposta.data_aposta else "",
            "is_winner": aposta.is_winner,
            "valor_premio": aposta.valor_premio,
            "acertos": acertos if acertos > 0 else aposta.acertos
        })
    
    return templates.TemplateResponse(
        "contest_detail.html",
        {
            "request": request,
            "concurso": concurso,
            "apostas": apostas_formatadas,
            "total_apostas": total_apostas,
            "total_arrecadado": total_arrecadado,
            "jogadores_unicos": jogadores_unicos,
            "total_ganhadores": total_ganhadores,
            "premio_distribuido": premio_distribuido,
            "numeros_sorteados": numeros_sorteados
        }
    )


@router.post("/concursos/{concurso_id}/sorteio")
async def realizar_sorteio(
    concurso_id: int,
    request: Request,
    numeros_sorteados: str = Form(...),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Realizar sorteio e calcular prêmios"""
    result = await db.execute(
        select(Concurso).where(Concurso.id == concurso_id)
    )
    concurso = result.scalar_one_or_none()
    
    if not concurso:
        raise HTTPException(status_code=404, detail="Concurso não encontrado")
    
    if concurso.is_drawn:
        raise HTTPException(status_code=400, detail="Este concurso já foi sorteado")
    
    if not concurso.is_active:
        raise HTTPException(status_code=400, detail="Este concurso não está ativo")
    
    try:
        # Validar e salvar números sorteados com Pydantic
        try:
            numeros_raw = json.loads(numeros_sorteados)
        except json.JSONDecodeError:
            raise ValueError("Formato de números inválido não é um JSON válido")

        validated_data = DrawNumbersSchema(**numeros_raw)
        
        white = validated_data.white
        powerball = validated_data.powerball

        concurso.numeros_sorteados = validated_data.model_dump_json()
        concurso.is_drawn = True
        concurso.is_active = False
        concurso.status = StatusConcurso.SORTEADO
        concurso.data_sorteio_realizado = datetime.utcnow()
        
        # Buscar todas as apostas do concurso
        result = await db.execute(
            select(Aposta)
            .options(selectinload(Aposta.usuario))
            .where(Aposta.concurso_id == concurso_id)
            .order_by(Aposta.data_aposta.asc())  # Ordenar por data para distribuir centavos
        )
        apostas = result.scalars().all()
        
        # Identificar ganhadores
        # Números oficiais sorteados: 5 brancos + 1 Powerball
        # Apostas dos jogadores: 20 brancos + 5 Powerballs
        # Ganhador: acertou os 5 brancos oficiais + o 1 Powerball oficial
        ganhadores = []
        numeros_brancos_oficiais = set(white)  # 5 números oficiais
        powerball_oficial = powerball[0] if powerball else None  # 1 Powerball oficial
        
        for aposta in apostas:
            try:
                numeros_brancos_aposta = json.loads(aposta.numeros_brancos)  # 20 números do jogador
                numeros_vermelhos_aposta = json.loads(aposta.numeros_vermelhos)  # 5 Powerballs do jogador
            except:
                continue
            
            # Calcular acertos: quantos dos 5 brancos oficiais o jogador acertou
            acertos_brancos = len(set(numeros_brancos_aposta) & numeros_brancos_oficiais)
            # Verificar se acertou o Powerball oficial
            acertou_powerball = powerball_oficial in numeros_vermelhos_aposta
            
            # Total de acertos: brancos acertados + 1 se acertou Powerball
            acertos_total = acertos_brancos + (1 if acertou_powerball else 0)
            
            aposta.acertos = acertos_total
            
            # Ganhador: acertou os 5 brancos oficiais + o Powerball oficial (6 acertos)
            if acertos_brancos == 5 and acertou_powerball:
                ganhadores.append(aposta)
                aposta.is_winner = True
        
        # Calcular e distribuir prêmios
        if ganhadores:
            premio_por_ganhador = concurso.premio_total / len(ganhadores)
            premio_base = int(premio_por_ganhador * 100) / 100  # Arredondar para 2 casas decimais
            centavos_restantes = int((concurso.premio_total - (premio_base * len(ganhadores))) * 100)
            
            # Distribuir prêmios
            for idx, ganhador in enumerate(ganhadores):
                valor_premio = premio_base
                if idx < centavos_restantes:
                    valor_premio += 0.01
                
                ganhador.valor_premio = round(valor_premio, 2)
                ganhador.cota_ganhadora = idx + 1
                
                # Atualizar saldo do usuário
                if ganhador.usuario:
                    ganhador.usuario.saldo += valor_premio
        
        await db.commit()
        
        return RedirectResponse(url=f"/admin/concursos/{concurso_id}", status_code=303)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato de números inválido (deve ser JSON)")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao realizar sorteio: {str(e)}")


@router.get("/concursos/{concurso_id}/exportar-csv")
async def exportar_csv(
    concurso_id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Exportar apostas do concurso para CSV"""
    result = await db.execute(
        select(Concurso).where(Concurso.id == concurso_id)
    )
    concurso = result.scalar_one_or_none()
    
    if not concurso:
        raise HTTPException(status_code=404, detail="Concurso não encontrado")
    
    # Buscar apostas
    result = await db.execute(
        select(Aposta)
        .options(selectinload(Aposta.usuario))
        .where(Aposta.concurso_id == concurso_id)
        .order_by(Aposta.data_aposta.desc())
    )
    apostas = result.scalars().all()
    
    # Criar CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho
    writer.writerow([
        "ID", "Usuário", "Telegram ID", "Números Brancos", "Números Vermelhos",
        "Valor Pago", "Data Aposta", "Acertos", "Ganhador", "Valor Prêmio"
    ])
    
    # Dados
    numeros_sorteados = []
    if concurso.numeros_sorteados:
        try:
            numeros_sorteados = json.loads(concurso.numeros_sorteados)
        except:
            pass
    
    for aposta in apostas:
        try:
            numeros_brancos = json.loads(aposta.numeros_brancos)
            numeros_vermelhos = json.loads(aposta.numeros_vermelhos)
        except:
            numeros_brancos = []
            numeros_vermelhos = []
        
        acertos = aposta.acertos
        if not acertos and numeros_sorteados:
            todos_numeros = numeros_brancos + numeros_vermelhos
            acertos = len(set(todos_numeros) & set(numeros_sorteados))
        
        writer.writerow([
            aposta.id,
            aposta.usuario.nome if aposta.usuario else "Desconhecido",
            aposta.usuario.telegram_id if aposta.usuario else "",
            ",".join(map(str, numeros_brancos)),
            ",".join(map(str, numeros_vermelhos)),
            f"{aposta.valor_pago:.2f}",
            aposta.data_aposta.strftime("%d/%m/%Y %H:%M") if aposta.data_aposta else "",
            acertos,
            "Sim" if aposta.is_winner else "Não",
            f"{aposta.valor_premio:.2f}" if aposta.is_winner else "0.00"
        ])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=concurso_{concurso_id}_apostas.csv"
        }
    )


@router.get("/api/powerball-result")
async def get_official_powerball_result(
    admin: Admin = Depends(get_current_admin)
):
    """Busca o resultado oficial mais recente da Powerball"""
    from services.powerball_results import powerball_service
    
    result = await powerball_service.get_latest_result()
    next_draw = await powerball_service.get_next_drawing()
    
    if not result:
        # Retornar dados simulados em caso de falha (para teste)
        return {
            "success": False,
            "message": "Não foi possível buscar o resultado oficial. Tente novamente mais tarde."
        }
        
    return {
        "success": True,
        "data": result,
        "next_draw": next_draw
    }

