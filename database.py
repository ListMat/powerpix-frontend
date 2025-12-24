from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Float, ForeignKey, Enum as SQLEnum, Text, Boolean
from datetime import datetime
import enum
import json
from typing import Optional
import bcrypt
from config import get_settings

settings = get_settings()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class Base(DeclarativeBase):
    pass


class StatusSorteio(str, enum.Enum):
    ABERTO = "ABERTO"
    FECHADO = "FECHADO"


class StatusConcurso(str, enum.Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    SORTEADO = "SORTEADO"


class TipoPromocao(str, enum.Enum):
    FIXO = "FIXO"  # Desconto fixo em R$
    PERCENTUAL = "PERCENTUAL"  # Desconto percentual


class TipoTransacao(str, enum.Enum):
    DEPOSITO = "DEPOSITO"
    APOSTA = "APOSTA"
    PREMIO = "PREMIO"
    SAQUE = "SAQUE"


class StatusTransacao(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PAGO = "PAGO"
    FALHA = "FALHA"
    CANCELADO = "CANCELADO"


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)  # Obrigatório
    saldo = Column(Float, default=0.0, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    
    # Dados de cadastro obrigatórios
    cpf = Column(String(14), nullable=True)  # CPF para pagamentos (formato: 000.000.000-00)
    pix = Column(String(255), nullable=True)  # Chave PIX para receber prêmios
    telefone = Column(String(20), nullable=True)  # Número de telefone
    
    # Dados opcionais
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)  # UF (2 caracteres)
    
    # Flag para verificar se cadastro está completo
    cadastro_completo = Column(Boolean, default=False, nullable=False)
    
    # Soft delete - arquivamento de conta
    is_archived = Column(Boolean, default=False, nullable=False)
    data_arquivamento = Column(DateTime, nullable=True)
    
    # Foto de perfil do usuário
    photo_url = Column(String(255), nullable=True)  # Caminho relativo para a foto (ex: /static/avatars/123456.jpg)
    
    apostas = relationship("Aposta", back_populates="usuario")
    transacoes = relationship("Transacao", back_populates="usuario", cascade="all, delete-orphan")


class Sorteio(Base):
    __tablename__ = "sorteios"
    
    id = Column(Integer, primary_key=True, index=True)
    data = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(StatusSorteio), default=StatusSorteio.ABERTO, nullable=False)
    premio_base = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)  # Arrecadação (pode ser calculada dinamicamente)
    meta_arrecadacao = Column(Float, default=3000.0)
    taxa_inicial = Column(Float, default=0.3)
    taxa_pos_meta = Column(Float, default=0.9)
    numeros_sorteados = Column(Text, nullable=True)  # JSON string
    
    apostas = relationship("Aposta", back_populates="sorteio")


class Concurso(Base):
    __tablename__ = "concursos"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_sorteio_prevista = Column(DateTime, nullable=True)
    premio_total = Column(Float, default=0.0, nullable=False)
    preco_cota = Column(Float, default=25.00, nullable=False)
    status = Column(SQLEnum(StatusConcurso), default=StatusConcurso.ATIVO, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_drawn = Column(Boolean, default=False, nullable=False)
    numeros_sorteados = Column(Text, nullable=True)  # JSON string com 6 números
    data_sorteio_realizado = Column(DateTime, nullable=True)
    
    apostas = relationship("Aposta", back_populates="concurso", cascade="all, delete-orphan")
    promocoes = relationship("Promocao", back_populates="concurso", cascade="all, delete-orphan")


class Promocao(Base):
    __tablename__ = "promocoes"
    
    id = Column(Integer, primary_key=True, index=True)
    concurso_id = Column(Integer, ForeignKey("concursos.id"), nullable=False)
    tipo = Column(SQLEnum(TipoPromocao), nullable=False)
    valor = Column(Float, nullable=False)  # Valor fixo ou percentual
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    concurso = relationship("Concurso", back_populates="promocoes")


class Transacao(Base):
    __tablename__ = "transacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo = Column(SQLEnum(TipoTransacao), nullable=False)
    valor = Column(Float, nullable=False)
    status = Column(SQLEnum(StatusTransacao), default=StatusTransacao.PENDENTE, nullable=False)
    gateway_id = Column(String(255), nullable=True)  # ID da transação no gateway de pagamento
    descricao = Column(Text, nullable=True)  # Descrição adicional
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    usuario = relationship("Usuario", back_populates="transacoes")


class Aposta(Base):
    __tablename__ = "apostas"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    sorteio_id = Column(Integer, ForeignKey("sorteios.id"), nullable=True)  # Pode ser null se usar concurso
    concurso_id = Column(Integer, ForeignKey("concursos.id"), nullable=True)  # Novo campo para concursos
    numeros_brancos = Column(Text, nullable=False)  # JSON string
    numeros_vermelhos = Column(Text, nullable=False)  # JSON string
    valor_pago = Column(Float, nullable=False)
    data_aposta = Column(DateTime, default=datetime.utcnow)
    
    # Campos para ganhadores
    is_winner = Column(Boolean, default=False, nullable=False)
    cota_ganhadora = Column(Integer, nullable=True)  # Índice da cota que ganhou
    valor_premio = Column(Float, default=0.0, nullable=False)
    acertos = Column(Integer, default=0, nullable=False)  # Quantidade de números acertados
    
    usuario = relationship("Usuario", back_populates="apostas")
    sorteio = relationship("Sorteio", back_populates="apostas")
    concurso = relationship("Concurso", back_populates="apostas")


class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)


class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    default_pack_price = Column(Float, default=25.00, nullable=False)
    current_discount_percent = Column(Integer, default=0, nullable=False)
    override_price = Column(Float, default=0.0, nullable=False)  # Se > 0 e promo ativa, usa esse valor
    is_promo_active = Column(Boolean, default=False, nullable=False)


# Engine e Session
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Criar tabelas e admin padrão se não existir"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Migração: Adicionar colunas se não existirem (PostgreSQL)
    async with engine.begin() as conn:
        try:
            from sqlalchemy import text
            
            # Verificar se a coluna revenue existe na tabela sorteios
            result = await conn.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'sorteios' AND column_name = 'revenue'
                """)
            )
            if not result.fetchone():
                await conn.execute(text("ALTER TABLE sorteios ADD COLUMN revenue DOUBLE PRECISION DEFAULT 0.0"))
                print("✓ Coluna 'revenue' adicionada à tabela sorteios")
            
            # Verificar colunas na tabela apostas
            for col_name, col_type, default in [
                ('concurso_id', 'INTEGER', None),
                ('is_winner', 'BOOLEAN', 'FALSE'),
                ('cota_ganhadora', 'INTEGER', None),
                ('valor_premio', 'DOUBLE PRECISION', '0.0'),
                ('acertos', 'INTEGER', '0')
            ]:
                result = await conn.execute(
                    text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'apostas' AND column_name = '{col_name}'
                    """)
                )
                if not result.fetchone():
                    default_clause = f" DEFAULT {default}" if default else ""
                    await conn.execute(text(f"ALTER TABLE apostas ADD COLUMN {col_name} {col_type}{default_clause}"))
                    print(f"✓ Coluna '{col_name}' adicionada à tabela apostas")
            
            # Verificar colunas na tabela usuarios
            for col_name, col_type, default in [
                ('pix', 'VARCHAR(255)', None),
                ('telefone', 'VARCHAR(20)', None),
                ('cidade', 'VARCHAR(100)', None),
                ('estado', 'VARCHAR(2)', None),
                ('cadastro_completo', 'BOOLEAN', 'FALSE'),
                ('cpf', 'VARCHAR(14)', None),
                ('is_archived', 'BOOLEAN', 'FALSE'),
                ('data_arquivamento', 'TIMESTAMP', None),
                ('photo_url', 'VARCHAR(255)', None)
            ]:
                result = await conn.execute(
                    text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'usuarios' AND column_name = '{col_name}'
                    """)
                )
                if not result.fetchone():
                    default_clause = f" DEFAULT {default}" if default else ""
                    await conn.execute(text(f"ALTER TABLE usuarios ADD COLUMN {col_name} {col_type}{default_clause}"))
                    print(f"✓ Coluna '{col_name}' adicionada à tabela usuarios")
        except Exception as e:
            print(f"⚠ Aviso ao verificar/adicionar colunas: {e}")
    
    # Criar admin padrão se não existir
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        
        result = await session.execute(select(Admin).where(Admin.username == settings.ADMIN_USERNAME))
        admin = result.scalar_one_or_none()
        
        if not admin:
            password_hash = hash_password(settings.ADMIN_PASSWORD)
            new_admin = Admin(
                username=settings.ADMIN_USERNAME,
                password_hash=password_hash
            )
            session.add(new_admin)
            await session.commit()
            print(f"Admin padrão criado: {settings.ADMIN_USERNAME}")
        
        # Criar configuração padrão do sistema se não existir
        result = await session.execute(select(SystemConfig).limit(1))
        config = result.scalar_one_or_none()
        
        if not config:
            default_config = SystemConfig(
                default_pack_price=25.00,
                current_discount_percent=0,
                override_price=0.0,
                is_promo_active=False
            )
            session.add(default_config)
            await session.commit()
            print("Configuração padrão do sistema criada")

