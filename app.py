from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import logging
from contextlib import asynccontextmanager

from database import init_db
from template_config import templates  # Importar templates configurado
from routers import bot, webapp, admin, api, finance, player
from config import get_settings

settings = get_settings()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    logger.info("Inicializando banco de dados...")
    await init_db()
    logger.info("Banco de dados inicializado!")
    
    # Configurar webhook do Telegram se WEBHOOK_URL estiver configurado
    if settings.WEBHOOK_URL:
        from routers.bot import bot
        webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}/{settings.BOT_TOKEN}"
        try:
            await bot.set_webhook(webhook_url)
            logger.info(f"Webhook configurado: {webhook_url}")
        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}")
    
    yield
    
    # Shutdown
    logger.info("Encerrando aplicação...")
    if settings.WEBHOOK_URL:
        from routers.bot import bot
        try:
            await bot.delete_webhook()
            logger.info("Webhook removido")
        except Exception as e:
            logger.error(f"Erro ao remover webhook: {e}")


# Criar aplicação FastAPI
app = FastAPI(
    title="PowerPix",
    description="Sistema de Loteria - Telegram Mini App + Admin Dashboard",
    lifespan=lifespan
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Registrar routers
app.include_router(bot.router, tags=["bot"])
app.include_router(webapp.router, tags=["webapp"])
app.include_router(admin.router, tags=["admin"])
app.include_router(api.router, tags=["api"])
app.include_router(finance.router, tags=["finance"])
app.include_router(player.router, tags=["player"])


@app.get("/")
async def root():
    """Rota raiz - redireciona para login admin"""
    return RedirectResponse(url="/admin/login")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "powerpix"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

