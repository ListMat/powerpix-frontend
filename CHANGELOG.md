# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2025-12-04

### Adicionado
- Interface de seleção PowerPix com 69 números brancos e 26 powerballs vermelhas
- Sistema de seleção manual de até 20 números e 5 powerballs
- Função "Palpite Mágico" para geração aleatória de apostas
- Integração com Telegram Web App (feedback háptico e tema)
- Contador visual de números selecionados
- Validação automática antes de confirmar aposta
- Design responsivo com cores temáticas (azul marinho, verde neon, vermelho)
- Prevenção de zoom indesejado em dispositivos móveis
- Backend Python com FastAPI
- Sistema de carteira e pagamentos integrado com ASAAS
- Sistema de administração de concursos
- Banco de dados SQLite

### Segurança
- Configurações sensíveis em arquivo `.env`
- Proteção de rotas administrativas

