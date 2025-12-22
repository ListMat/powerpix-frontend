"""
Configuração centralizada de templates Jinja2
"""
from fastapi.templating import Jinja2Templates

# Instância compartilhada de templates
templates = Jinja2Templates(directory="templates")

# Filtros customizados para Jinja2
def format_currency_br(value):
    """Formata valor para moeda brasileira (R$ 1.234,56)"""
    try:
        if value is None:
            return "R$ 0,00"
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"R$ {value}"

# Registrar filtros globalmente
templates.env.filters["currency"] = format_currency_br

