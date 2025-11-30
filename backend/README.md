# 🐍 Backend do Didin Fácil

Este diretório contém a API, workers e scrapers do projeto Didin Fácil.

## 🏗️ Estrutura

- **`api/`**: Aplicação FastAPI (endpoints, rotas).
- **`scraper/`**: Módulos de scraping (Playwright, BeautifulSoup).
- **`workers/`**: Celery workers para tarefas em background.
- **`integrations/`**: Integrações com serviços externos (TikTok, etc).
- **`modules/`**: Módulos de lógica de negócio.
- **`alembic/`**: Migrações de banco de dados.
- **`tests/`**: Testes automatizados (Pytest).

## 🚀 Como Rodar

### Pré-requisitos
- Python 3.11+
- PostgreSQL
- Redis

### Instalação

1. Crie um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   Copie `.env.staging.example` para `.env` e ajuste os valores.

4. Execute as migrações:
   ```bash
   alembic upgrade head
   ```

5. Inicie a API:
   ```bash
   uvicorn api.main:app --reload
   ```

## 🧪 Testes

Para rodar os testes:
```bash
pytest
```
