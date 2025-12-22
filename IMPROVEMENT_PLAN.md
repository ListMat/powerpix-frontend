# Relatório de Análise e Plano de Melhorias - PowerPix UI

## 1. Visão Geral
O projeto **PowerPix** é um sistema de loteria híbrido composto por:
- **Backend**: FastAPI (Python) com SQLite/SQLAlchemy.
- **Frontend Admin**: Renderizado server-side (Jinja2).
- **Frontend App (Telegram)**: Single Page App (SPA) em HTML/JS puro (`powerpix-front`).

## 2. Diagnóstico

### Pontos Fortes
- **Estrutura do Backend**: Uso correto de `routers` e `lifespan` no FastAPI.
- **Integração de Pagamentos**: Serviço `asaas.py` bem estruturado.
- **Logging**: Configurado e funcional.

### Áreas de Melhoria Crítica

#### A. Frontend (Nível: Alto)
O frontend atual do usuário (`powerpix-front/index.html`) é um arquivo único "monolítico".
- **Problema**: Difícil de manter, escalar e testar. O estado é gerenciado globalmente.
- **Solução Recomendada**: Migrar para uma aplicação **React** moderna (usando Vite ou Next.js).
    - Permitirá componentes reutilizáveis (Botões, Bolas, Modais).
    - Melhor gerenciamento de estado (React Hooks).
    - Design System consistente (TailwindC SS).

#### B. Backend - Estrutura e Validação (Nível: Médio)
O arquivo `routers/admin.py` está sobrecarregado (God Object / Fat Controller).
- **Problema**: Mistura lógica de banco de dados, regras de negócio (sorteio, premiação) e apresentação.
- **Validação Manual**: As rotas usam `json.loads` manual e validação `if/else` complexa.
- **Solução Recomendada**:
    1.  **Schemas Pydantic**: Mover validação de dados para classes Pydantic.
    2.  **Services**: Mover lógica de negócios (Ex: `realizar_sorteio`, `calcular_premios`) para `services/lottery_service.py`.

#### C. Banco de Dados (Nível: Médio)
- **SQLite**: Adequado para desenvolvimento, mas arriscado para produção (concorrência e integridade de dados financeiros).
- **Recomendação**: Migrar para **PostgreSQL** para ambiente de produção.

#### D. Testes (Nível: Alto)
- **Ausência de Testes**: Não foram identificados testes automatizados.
- **Risco**: Regras financeiras e de sorteio sem cobertura de testes podem gerar prejuízos.
- **Recomendação**: Implementar `pytest` cobrindo pelo menos:
    - Cálculo de prêmios.
    - Fluxo de apostas.
    - Webhooks de pagamento.

---

## 3. Plano de Ação Imediato

Como parte desta análise, realizei a seguinte melhoria demonstrativa no código:

### Refatoração: Validação Robusta com Pydantic
Refatorei a lógica de validação dos números sorteados em `routers/admin.py`.
- **Antes**: Validação manual com múltiplos `if/else` e `json.loads`.
- **Depois**: Uso de **Pydantic Models** (`schemas.py`) para garantir integridade e tipagem automática.

### Próximos Passos Sugeridos
1.  **Aprovar a criação do novo Frontend em React** (`powerpix-next`).
2.  Continuar a extração de lógica de `admin.py` para `services/`.
3.  Configurar suite de testes (`tests/`).
