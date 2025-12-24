"""Script para testar se o webhook está configurado corretamente"""
import asyncio
from config import get_settings
from routers.bot import bot

settings = get_settings()

async def test_webhook():
    """Testa a configuração do webhook"""
    print("=" * 80)
    print("Teste de Configuração do Webhook")
    print("=" * 80)
    
    try:
        # Verificar informações do webhook
        webhook_info = await bot.get_webhook_info()
        
        print(f"\nInformacoes do Webhook:")
        print(f"   URL: {webhook_info.url or 'Nenhum webhook configurado'}")
        print(f"   Pending Updates: {webhook_info.pending_update_count}")
        print(f"   Last Error Date: {webhook_info.last_error_date}")
        print(f"   Last Error Message: {webhook_info.last_error_message or 'Nenhum erro'}")
        print(f"   Max Connections: {webhook_info.max_connections}")
        
        # Verificar URL esperada
        if settings.WEBHOOK_URL:
            expected_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}/{settings.BOT_TOKEN}"
            print(f"\nURL Esperada: {expected_url}")
            
            if webhook_info.url == expected_url:
                print("OK: Webhook esta configurado corretamente!")
            else:
                print("AVISO: Webhook nao esta configurado com a URL esperada!")
                print(f"   Esperado: {expected_url}")
                print(f"   Atual: {webhook_info.url}")
        else:
            print("\nAVISO: WEBHOOK_URL nao esta configurado no .env")
        
        # Verificar se há updates pendentes
        if webhook_info.pending_update_count > 0:
            print(f"\nAVISO: Ha {webhook_info.pending_update_count} update(s) pendente(s)!")
            print("   Isso pode indicar que o webhook nao esta processando updates corretamente.")
        
        # Verificar erros
        if webhook_info.last_error_message:
            print(f"\nERRO: Ultimo erro do webhook:")
            print(f"   Data: {webhook_info.last_error_date}")
            print(f"   Mensagem: {webhook_info.last_error_message}")
        
    except Exception as e:
        print(f"\nERRO ao verificar webhook: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_webhook())

