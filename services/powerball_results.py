import httpx
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PowerballScraper:
    """Serviço para buscar resultados oficiais da Powerball"""
    
    BASE_URL = "https://www.powerball.com"
    
    async def get_latest_result(self) -> Optional[Dict[str, Any]]:
        """
        Busca o resultado mais recente da Powerball.
        Retorna um dicionário com:
        - data: Data do sorteio
        - white: Lista de 5 números brancos
        - powerball: Número vermelho (Powerball)
        """
        try:
            # Usar uma API pública alternativa se o scraping direto falhar ou for bloqueado
            # A API oficial do powerball.com é protegida, mas eles tem um endpoint JSON público
            # Endpoint: https://www.powerball.com/api/v1/numbers/powerball/recent?_format=json
            
            url = "https://www.powerball.com/api/v1/numbers/powerball/recent?_format=json"
            
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        latest = data[0]
                        
                        # Parse números "11, 23, 45, 67, 89" e Powerball "12"
                        # O formato da API pode variar, vamos tratar com cuidado
                        field_winning_numbers = latest.get('field_winning_numbers', '')
                        if ',' in field_winning_numbers:
                            white_numbers = [int(n.strip()) for n in field_winning_numbers.split(',')]
                        else:
                            # Tentar separar por espaço se não tiver vírgula
                            white_numbers = [int(n.strip()) for n in field_winning_numbers.split(' ') if n.strip()]
                            
                        # Pegar apenas os 5 primeiros se vierem juntos
                        if len(white_numbers) > 5:
                            powerball = white_numbers[-1]
                            white_numbers = white_numbers[:5]
                        else:
                            # Tentar pegar do campo específico se existir
                            powerball = int(latest.get('field_powerball', '0'))

                        date_str = latest.get('field_draw_date', '')
                        
                        return {
                            "data": date_str,
                            "white": sorted(white_numbers),
                            "powerball": [powerball]  # Lista para manter compatibilidade com nosso sistema
                        }
            
            # Fallback: Scraping do site lotteryusa.com (mais simples de fazer parse)
            return await self._scrape_fallback()
            
        except Exception as e:
            logger.error(f"Erro ao buscar resultados da Powerball: {e}")
            # Tentar fallback em caso de erro na API
            return await self._scrape_fallback()

    async def get_next_drawing(self) -> Optional[Dict[str, Any]]:
        """
        Busca informações sobre o próximo sorteio.
        Retorna:
        - date: Data do próximo sorteio (YYYY-MM-DD)
        - jackpot: Valor estimado do prêmio
        """
        try:
            # API oficial para estimativas de jackpot
            url = "https://www.powerball.com/api/v1/estimates/powerball?_format=json"
            
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        next_draw = data[0]
                        return {
                            "date": next_draw.get('field_next_draw_date'),
                            "jackpot": next_draw.get('field_next_jackpot_amount', 'N/A')
                        }
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar próximo sorteio: {e}")
            return None

    async def _scrape_fallback(self) -> Optional[Dict[str, Any]]:
        """Fallback usando scraping de site de terceiros"""
        try:
            url = "https://www.lotteryusa.com/powerball/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Procurar containers de números
                    # A estrutura pode mudar, mas geralmente são listas ul/li com classes específicas
                    
                    # Exemplo genérico de busca
                    numbers_container = soup.find('ul', class_='draw-result')
                    if not numbers_container:
                        # Tentar outra classe comum
                        numbers_container = soup.find(class_='c-draw-result')
                    
                    white_numbers = []
                    powerball = None
                    
                    if numbers_container:
                        items = numbers_container.find_all('li')
                        for item in items:
                            text = item.get_text(strip=True)
                            if text.isdigit():
                                if 'powerball' in item.get('class', []) or 'bonus' in item.get('class', []):
                                    powerball = int(text)
                                else:
                                    white_numbers.append(int(text))
                    
                    # Se não achou na estrutura, tentar regex no texto cru (último recurso)
                    if not white_numbers:
                        import re
                        # Procurar padrão de data e números
                        # Ex: "Winning Numbers: 10 20 30 40 50 Powerball: 15"
                        pass

                    if white_numbers and powerball:
                        return {
                            "data": datetime.now().strftime("%Y-%m-%d"), # Data aproximada
                            "white": sorted(white_numbers[:5]),
                            "powerball": [powerball]
                        }
                        
            return None
        except Exception as e:
            logger.error(f"Erro no fallback scraping: {e}")
            return None

# Instância global
powerball_service = PowerballScraper()

