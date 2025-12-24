"""Script para configurar o webhook manualmente"""
import asyncio
from config import get_settings
from routers.bot import bot

settings = get_settings()

async def setup_webhook():
    """Configura o webhook manualmente"""
    print("=" * 80)
    print("Configurando Webhook")
    print("=" * 80)
    
    if not settings.WEBHOOK_URL:
        print("\nERRO: WEBHOOK_URL nao esta configurado no .env")
        return
    
    webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}/{settings.BOT_TOKEN}"
    print(f"\nConfigurando webhook: {webhook_url}")
    
    try:
        await bot.set_webhook(webhook_url)
        print("OK: Webhook configurado com sucesso!")
        
        # Verificar se foi configurado
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url == webhook_url:
            print(f"OK: Webhook verificado: {webhook_info.url}")
        else:
            print(f"AVISO: Webhook pode nao estar configurado corretamente.")
            print(f"   Esperado: {webhook_url}")
            print(f"   Atual: {webhook_info.url}")
    except Exception as e:
        print(f"ERRO ao configurar webhook: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(setup_webhook())

