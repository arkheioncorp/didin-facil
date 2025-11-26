# 🚀 Guia de Lançamento Oficial - TikTrend Finder

Este guia descreve os passos finais para preparar, construir e distribuir a versão 1.0 do TikTrend Finder.

## 1. Configuração de Produção

Antes de gerar os binários finais, certifique-se de que as variáveis de ambiente e configurações estão corretas.

### Backend (.env)
Certifique-se de que o arquivo `.env` no servidor de produção contenha chaves reais e seguras:
- `JWT_SECRET`: Gere uma chave forte (`openssl rand -hex 32`).
- `OPENAI_API_KEY`: Chave de produção da OpenAI.
- `MP_ACCESS_TOKEN`: Token de produção do Mercado Pago (não Sandbox).
- `POSTHOG_API_KEY`: Chave de projeto do PostHog para analytics.
- `SAFETY_SWITCH_ENABLED=true`: Para proteção do scraper.

### Frontend (Tauri)
Verifique `src-tauri/tauri.conf.json`:
- `identifier`: Deve ser único (ex: `com.didinfacil.tiktrend`).
- `version`: Deve ser `1.0.0`.
- `bundle`: Certifique-se de que os ícones estão corretos em `src-tauri/icons/`.

## 2. Assinatura de Código (Code Signing)

Para evitar avisos de "Editor Desconhecido" (Windows) ou bloqueios (macOS), você deve assinar o aplicativo.

### Windows
1. Obtenha um certificado EV ou Standard Code Signing.
2. Configure as variáveis de ambiente antes do build:
   ```bash
   export TAURI_SIGNING_PRIVATE_KEY="caminho/para/chave"
   export TAURI_SIGNING_PASSWORD="senha"
   ```

### macOS
1. Inscreva-se no Apple Developer Program.
2. Gere os certificados "Developer ID Application".
3. O Tauri usará automaticamente se estiverem no Keychain, ou configure via variáveis de ambiente.

## 3. Gerando os Binários (Build)

Execute o comando de build otimizado para produção:

```bash
# Limpar builds anteriores
rm -rf src-tauri/target/

# Instalar dependências limpas
npm ci

# Build final
npm run tauri:build
```

Os instaladores serão gerados em:
- **Windows:** `src-tauri/target/release/bundle/msi/` e `nsis/`
- **macOS:** `src-tauri/target/release/bundle/dmg/` e `app/`
- **Linux:** `src-tauri/target/release/bundle/deb/` e `appimage/`

## 4. Deploy do Backend

O backend deve ser implantado em uma infraestrutura escalável (Railway, AWS, DigitalOcean).

1. **Build Docker:**
   ```bash
   docker build -t tiktrend-api -f docker/api.Dockerfile .
   docker build -t tiktrend-scraper -f docker/scraper.Dockerfile .
   ```

2. **Database Migrations:**
   Certifique-se de que o banco de produção está inicializado com `docker/init.sql`.

## 5. Checklist de Lançamento

- [ ] **Analytics:** Verificar se eventos estão chegando no PostHog.
- [ ] **Pagamentos:** Testar fluxo real de compra (R$ 1,00 ou cupom de 100%).
- [ ] **Scraper:** Verificar se proxies estão ativos e rotacionando.
- [ ] **Update Server:** Configurar endpoint para atualizações automáticas (Tauri Updater).
- [ ] **Termos de Uso:** Garantir que Links para Termos e Privacidade funcionam no App.

## 6. Próximos Passos (Pós-Lançamento)

1. **Monitoramento:** Acompanhar logs de erro no Sentry (se configurado) ou logs do container.
2. **Marketing:** Lançar landing page apontando para os downloads.
3. **Suporte:** Canal de atendimento para usuários (Discord/WhatsApp).

---
**Parabéns!** O TikTrend Finder está pronto para o mundo. 🚀
