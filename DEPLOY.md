# Guia de Deploy no Railway - TikTrend Finder

Este guia descreve os passos para realizar o deploy da aplicação (Backend + Frontend) no Railway.

## 1. Preparação dos Arquivos (Já realizado)

O assistente já realizou as seguintes configurações no código:

1.  **Backend Dockerfile (`docker/api.Dockerfile`):** Atualizado para incluir pastas ausentes (`vendor`, `integrations`, `scraper`, `seller_bot`).
2.  **Frontend Dockerfile (`docker/frontend.Dockerfile`):** Criado para buildar o React/Vite e servir com Nginx.
3.  **Nginx Config (`docker/nginx.conf`):** Criado para servir o frontend e lidar com rotas SPA.
4.  **Configuração do Banco (`backend/shared/config.py`):** Adicionado validador para corrigir URLs `postgres://` do Railway para `postgresql://` (necessário para `asyncpg`).

## 2. Configuração no Railway

Você precisará criar **dois serviços** no seu projeto do Railway: um para o Backend e outro para o Frontend.

### Serviço 1: Backend (API)

1.  **Novo Serviço:** Selecione "GitHub Repo" e escolha o repositório `tiktrend-facil`.
2.  **Configurações (Settings):**
    *   **Root Directory:** `/` (pode deixar vazio/padrão)
    *   **Build Command:** (Deixe vazio, usaremos Dockerfile)
    *   **Start Command:** (Deixe vazio, definido no Dockerfile/railway.toml)
    *   **Dockerfile Path:** `docker/api.Dockerfile`
3.  **Variáveis (Variables):**
    *   Copie o conteúdo de `docker/railway.env.template`.
    *   **IMPORTANTE:** Gere um novo `JWT_SECRET_KEY` (`openssl rand -hex 32`).
    *   Adicione o plugin **PostgreSQL** no Railway. O Railway injetará `DATABASE_URL` automaticamente.
    *   Adicione o plugin **Redis** no Railway. O Railway injetará `REDIS_URL` automaticamente.
4.  **Networking:**
    *   Gere um domínio (ex: `tiktrend-backend.up.railway.app`).

### Serviço 2: Frontend (React) - Opção Railway

1.  **Novo Serviço:** Selecione o **mesmo** repositório `tiktrend-facil`.
2.  **Configurações (Settings):**
    *   **Root Directory:** `/`
    *   **Dockerfile Path:** `docker/frontend.Dockerfile`
3.  **Variáveis (Variables):**
    *   `VITE_API_URL`: A URL do seu backend (ex: `https://tiktrend-backend.up.railway.app`).
    *   **Nota:** Como é um build estático (Vite), essa variável precisa estar presente **durante o build**. Se mudar a URL, precisa redeployar o frontend.
4.  **Networking:**
    *   Gere um domínio (ex: `tiktrend-facil.up.railway.app`).

### Serviço 2: Frontend (React) - Opção Vercel (Recomendado)

Se você já conectou o frontend no Vercel:

1.  **Environment Variables:**
    *   Vá em **Settings > Environment Variables**.
    *   Adicione `VITE_API_URL` com o valor da URL do seu backend no Railway (ex: `https://tiktrend-backend.up.railway.app`).
2.  **Redeploy:**
    *   Vá em **Deployments** e force um redeploy para que a nova variável seja injetada no build.
3.  **CORS (Backend):**
    *   O backend já foi configurado para aceitar conexões de `https://*.vercel.app`.
    *   Se tiver problemas de CORS, adicione a variável `CORS_ORIGINS` no Railway com o domínio exato do seu frontend (ex: `https://tiktrend-facil.vercel.app`).

## 3. Testando o Deploy

1.  Acesse a URL do Frontend.
2.  Tente fazer login.
3.  Verifique se as requisições estão indo para a URL correta do backend (Network tab do navegador).
4.  Verifique os logs do Backend no Railway se houver erros 500.

## 4. Migrações de Banco de Dados

O comando de inicialização do backend (`startCommand` no `railway.toml`) já inclui:
`alembic upgrade head`

Isso garante que as migrações rodem automaticamente a cada deploy.

## 5. Observações

*   **Workers:** Se precisar de workers em background (Celery/Redis Queue), crie um terceiro serviço usando o mesmo `docker/api.Dockerfile` mas com um comando de start diferente (ex: `celery -A ...`).
*   **Scraper:** O scraper roda dentro do backend ou workers. Certifique-se de que o container tenha recursos suficientes (RAM) se for usar Chrome Headless (o Dockerfile instala dependências básicas, mas para Chrome completo pode precisar de ajustes).
