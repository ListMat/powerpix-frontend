"""
Integração com Asaas Gateway de Pagamentos
Documentação: https://docs.asaas.com/
"""
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class AsaasService:
    """Serviço para integração com Asaas"""
    
    def __init__(self):
        self.api_url = settings.ASAAS_API_URL
        self.api_key = settings.ASAAS_API_KEY
        self.headers = {
            "access_token": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_pix_payment(
        self,
        customer_id: str,
        value: float,
        description: str,
        external_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria uma cobrança Pix no Asaas
        
        Args:
            customer_id: ID do cliente no Asaas
            value: Valor da cobrança
            description: Descrição da cobrança
            external_reference: Referência externa (ex: transaction_id)
        
        Returns:
            Dict com dados da cobrança criada
        """
        url = f"{self.api_url}/payments"
        
        payload = {
            "customer": customer_id,
            "billingType": "PIX",
            "value": value,
            "dueDate": datetime.now().strftime("%Y-%m-%d"),
            "description": description,
            "externalReference": external_reference
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Cobrança Pix criada no Asaas: {data.get('id')}")
                return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao criar cobrança Pix: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Erro ao criar cobrança: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao criar cobrança Pix: {e}")
            raise
    
    async def get_pix_qrcode(self, payment_id: str) -> Dict[str, Any]:
        """
        Obtém o QR Code Pix de uma cobrança
        
        Args:
            payment_id: ID da cobrança no Asaas
        
        Returns:
            Dict com payload (copia e cola) e encodedImage (base64 do QR Code)
        """
        url = f"{self.api_url}/payments/{payment_id}/pixQrCode"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"QR Code Pix obtido para cobrança: {payment_id}")
                return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao obter QR Code: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Erro ao obter QR Code: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao obter QR Code: {e}")
            raise
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Consulta o status de uma cobrança
        
        Args:
            payment_id: ID da cobrança no Asaas
        
        Returns:
            Dict com dados da cobrança
        """
        url = f"{self.api_url}/payments/{payment_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao consultar status: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Erro ao consultar status: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao consultar status: {e}")
            raise
    
    async def create_customer(
        self,
        name: str,
        cpf_cnpj: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        external_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um cliente no Asaas
        
        Args:
            name: Nome do cliente
            cpf_cnpj: CPF ou CNPJ
            email: Email
            phone: Telefone
            external_reference: Referência externa (ex: telegram_id)
        
        Returns:
            Dict com dados do cliente criado
        """
        url = f"{self.api_url}/customers"
        
        payload = {
            "name": name,
            "externalReference": external_reference
        }
        
        if cpf_cnpj:
            payload["cpfCnpj"] = cpf_cnpj
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Cliente criado no Asaas: {data.get('id')}")
                return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao criar cliente: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Erro ao criar cliente: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {e}")
            raise
    
    async def get_customer_by_external_reference(self, external_reference: str) -> Optional[Dict[str, Any]]:
        """
        Busca cliente por referência externa
        
        Args:
            external_reference: Referência externa (ex: telegram_id)
        
        Returns:
            Dict com dados do cliente ou None
        """
        url = f"{self.api_url}/customers"
        params = {"externalReference": external_reference}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("data") and len(data["data"]) > 0:
                    return data["data"][0]
                return None
        
        except Exception as e:
            logger.error(f"Erro ao buscar cliente: {e}")
            return None
    
    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Valida a assinatura do webhook do Asaas
        
        Args:
            payload: Corpo da requisição
            signature: Assinatura recebida no header
        
        Returns:
            True se válido, False caso contrário
        """
        # Asaas não usa assinatura por padrão, mas você pode configurar
        # um token secreto e validar aqui
        if settings.ASAAS_WEBHOOK_TOKEN:
            return signature == settings.ASAAS_WEBHOOK_TOKEN
        return True
    
    def map_asaas_status_to_internal(self, asaas_status: str) -> str:
        """
        Mapeia status do Asaas para status interno
        
        Status Asaas:
        - PENDING: Aguardando pagamento
        - RECEIVED: Pagamento recebido
        - CONFIRMED: Pagamento confirmado
        - OVERDUE: Vencido
        - REFUNDED: Estornado
        - RECEIVED_IN_CASH: Recebido em dinheiro
        - REFUND_REQUESTED: Estorno solicitado
        - CHARGEBACK_REQUESTED: Chargeback solicitado
        - CHARGEBACK_DISPUTE: Disputa de chargeback
        - AWAITING_CHARGEBACK_REVERSAL: Aguardando reversão de chargeback
        - DUNNING_REQUESTED: Recuperação solicitada
        - DUNNING_RECEIVED: Recuperação recebida
        - AWAITING_RISK_ANALYSIS: Aguardando análise de risco
        """
        status_map = {
            "PENDING": "PENDENTE",
            "RECEIVED": "PAGO",
            "CONFIRMED": "PAGO",
            "OVERDUE": "FALHA",
            "REFUNDED": "CANCELADO",
            "RECEIVED_IN_CASH": "PAGO",
            "AWAITING_RISK_ANALYSIS": "PENDENTE"
        }
        
        return status_map.get(asaas_status, "PENDENTE")


# Instância singleton
asaas_service = AsaasService()

