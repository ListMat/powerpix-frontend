"""Serviço para gerenciar fotos de perfil dos usuários"""
import logging
from pathlib import Path
from aiogram import Bot
from typing import Optional

logger = logging.getLogger(__name__)

# Diretório para armazenar avatares
AVATARS_DIR = Path("static/avatars")
AVATARS_DIR.mkdir(parents=True, exist_ok=True)


async def download_user_photo(bot: Bot, user_id: int) -> Optional[str]:
    """
    Baixa a foto de perfil do usuário do Telegram e salva localmente.
    
    Args:
        bot: Instância do bot do Telegram
        user_id: ID do usuário no Telegram
        
    Returns:
        Caminho relativo da foto salva (ex: /static/avatars/123456.jpg) ou None se não houver foto
    """
    try:
        # Buscar fotos de perfil do usuário
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        
        if not photos.photos or len(photos.photos) == 0:
            logger.info(f"Usuário {user_id} não tem foto de perfil")
            return None
        
        # Pegar a foto menor (thumbnail) - geralmente é suficiente para avatar
        photo = photos.photos[0][0]  # Primeira foto, menor tamanho
        
        # Baixar o arquivo
        file = await bot.get_file(photo.file_id)
        
        # Caminho de destino
        file_path = AVATARS_DIR / f"{user_id}.jpg"
        
        # Baixar e salvar
        await bot.download_file(file.file_path, str(file_path))
        
        logger.info(f"Foto de perfil baixada para usuário {user_id}: {file_path}")
        
        # Retornar caminho relativo para uso na web
        return f"/static/avatars/{user_id}.jpg"
        
    except Exception as e:
        logger.error(f"Erro ao baixar foto de perfil do usuário {user_id}: {e}", exc_info=True)
        return None



