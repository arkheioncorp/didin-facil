# 🐳 Docker & Infraestrutura

Este diretório contém as configurações de containerização e orquestração do TikTrend Finder.

## 📂 Estrutura

- **`docker-compose.yml`**: Configuração base para desenvolvimento local.
- **`docker-compose.production.yml`**: Configuração para ambiente de produção.
- **`api.Dockerfile`**: Imagem Docker da API Backend.
- **`scraper.Dockerfile`**: Imagem Docker do Scraper.
- **`observability.yml`**: Configuração do stack de monitoramento (Prometheus, Grafana).
- **`meilisearch.yml`**: Configuração do motor de busca.
- **`grafana/`**: Dashboards e configurações do Grafana.
- **`prometheus.yml`**: Configuração do Prometheus.

## 🚀 Como Rodar com Docker

### Desenvolvimento

Para subir todo o ambiente de desenvolvimento (Banco, Redis, API, Workers):

```bash
docker-compose up -d
```

### Produção

Para subir o ambiente de produção:

```bash
docker-compose -f docker-compose.production.yml up -d
```

### Serviços Incluídos

- **API**: Backend FastAPI
- **Worker**: Celery Workers
- **PostgreSQL**: Banco de dados principal
- **Redis**: Cache e Broker de mensagens
- **MeiliSearch**: Motor de busca full-text
- **Prometheus/Grafana**: Monitoramento
