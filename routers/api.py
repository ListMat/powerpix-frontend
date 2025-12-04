from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import SystemConfig, get_db
from typing import Dict

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/current-price")
async def get_current_price(db: AsyncSession = Depends(get_db)) -> Dict[str, float]:
    """
    Endpoint para obter o preço atual do pack de apostas.
    
    Lógica de cálculo:
    1. Se override_price > 0 e is_promo_active == True: retorna override_price
    2. Senão, se current_discount_percent > 0 e is_promo_active == True: 
       retorna default_pack_price * (1 - desconto/100)
    3. Caso contrário: retorna default_pack_price (R$ 25.00)
    """
    # Buscar configuração do sistema (deve existir apenas uma)
    result = await db.execute(select(SystemConfig).limit(1))
    config = result.scalar_one_or_none()
    
    if not config:
        # Se não existir configuração, retornar preço padrão
        return {
            "price": 25.00,
            "default_price": 25.00,
            "discount_percent": 0,
            "is_promo_active": False
        }
    
    # Calcular preço final
    final_price = config.default_pack_price
    
    if config.is_promo_active:
        if config.override_price > 0:
            # Prioridade: override_price se definido e promo ativa
            final_price = config.override_price
        elif config.current_discount_percent > 0:
            # Aplicar desconto percentual
            discount_factor = 1 - (config.current_discount_percent / 100)
            final_price = config.default_pack_price * discount_factor
    
    return {
        "price": round(final_price, 2),
        "default_price": config.default_pack_price,
        "discount_percent": config.current_discount_percent,
        "override_price": config.override_price if config.override_price > 0 else None,
        "is_promo_active": config.is_promo_active
    }

