# Configuração do YouTube OAuth - TikTrend Finder

Este guia explica como configurar as credenciais do YouTube para fazer upload de vídeos.

## Passo 1: Criar Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Clique em **Criar Projeto**
3. Nome: `TikTrend Finder YouTube`
4. Clique em **Criar**

## Passo 2: Ativar YouTube Data API v3

1. No menu lateral, vá em **APIs e Serviços** > **Biblioteca**
2. Pesquise por `YouTube Data API v3`
3. Clique em **Ativar**

## Passo 3: Configurar Tela de Consentimento OAuth

1. Vá em **APIs e Serviços** > **Tela de consentimento OAuth**
2. Selecione **Externo** (ou Interno se for G Suite)
3. Preencha:
   - Nome do app: `TikTrend Finder`
   - E-mail de suporte: seu email
   - Domínios autorizados: (deixe vazio para dev)
   - E-mail de contato do desenvolvedor: seu email
4. Clique em **Salvar e continuar**

### Escopos

Adicione os seguintes escopos:
- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube`
- `https://www.googleapis.com/auth/youtube.readonly`

### Usuários de Teste

1. Clique em **Adicionar usuários**
2. Adicione o email da conta Google que vai usar para upload
3. Clique em **Salvar e continuar**

## Passo 4: Criar Credenciais OAuth

1. Vá em **APIs e Serviços** > **Credenciais**
2. Clique em **Criar credenciais** > **ID do cliente OAuth**
3. Tipo de aplicativo: **Aplicativo de desktop**
4. Nome: `TikTrend Finder Desktop`
5. Clique em **Criar**
6. **Baixe o JSON** clicando no ícone de download

## Passo 5: Salvar Credenciais

1. Renomeie o arquivo baixado para `youtube_credentials.json`
2. Mova para: `backend/data/youtube_credentials.json`

O arquivo deve ter este formato:
```json
{
  "installed": {
    "client_id": "xxxxx.apps.googleusercontent.com",
    "project_id": "tiktrend-facil-youtube",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-xxxxx",
    "redirect_uris": ["http://localhost"]
  }
}
```

## Passo 6: Autenticar no App

1. Inicie o backend: `cd backend && uvicorn api.main:app --reload`
2. Acesse a página de YouTube no app
3. Clique em "Adicionar Conta YouTube"
4. Digite um nome para a conta (ex: "principal")
5. Uma janela do navegador abrirá para autorização
6. Faça login na conta Google e autorize
7. O token será salvo automaticamente

## Quota do YouTube

A API do YouTube tem limite de 10.000 unidades/dia:

| Operação | Custo |
|----------|-------|
| Upload de vídeo | ~1.600 |
| Atualizar metadados | 50 |
| Listar vídeos | 1 |
| Definir thumbnail | 50 |

**Uploads máximos por dia:** ~6 vídeos

## Troubleshooting

### Erro: "Access blocked: App is not verified"

1. Vá em **Tela de consentimento OAuth**
2. Adicione seu email como **Usuário de teste**
3. Durante o login, clique em **Avançado** > **Acessar TikTrend Finder (não seguro)**

### Erro: "Quota exceeded"

1. Verifique seu uso em **APIs e Serviços** > **YouTube Data API v3** > **Métricas**
2. Aguarde até meia-noite (horário do Pacífico) para reset
3. Ou solicite aumento de quota no Google Cloud

### Erro: "Token has been expired or revoked"

1. Delete o arquivo de token: `backend/data/youtube_tokens/{user_id}_{account_name}.json`
2. Faça a autenticação novamente

## Variáveis de Ambiente

Adicione ao seu `backend/.env`:

```env
# YouTube OAuth (do Google Cloud Console)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
```

---

**Última atualização:** Novembro 2025
