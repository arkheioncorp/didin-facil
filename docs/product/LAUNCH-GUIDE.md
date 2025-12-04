# 🚀 Guia Completo para Lançar o TikTrend Finder - 100% GRATUITO

Este guia mostra como lançar seu aplicativo para **Windows, Linux e macOS** sem gastar nada em hospedagem.

---

## 📋 Resumo - Tudo que você precisa (GRÁTIS)

| Serviço | Para que serve | Custo |
|---------|----------------|-------|
| **GitHub Releases** | Hospedar downloads (.exe, .deb, .dmg) | ✅ GRÁTIS |
| **GitHub Pages** | Hospedar a landing page | ✅ GRÁTIS |
| **GitHub Actions** | Build automático multiplataforma | ✅ GRÁTIS (2000 min/mês) |
| **Cloudflare** (opcional) | CDN + domínio personalizado | ✅ GRÁTIS |

---

## 🎯 Passo a Passo

### 1️⃣ Configurar GitHub Pages (Landing Page)

1. Vá em **Settings** do repositório
2. Clique em **Pages** (menu lateral)
3. Em **Source**, selecione **GitHub Actions**
4. O workflow `deploy-pages.yml` fará o deploy automático

**URL da sua página:** `https://arkheioncorp.github.io/tiktrend-facil/`

### 2️⃣ Fazer o Primeiro Release

```bash
# 1. Certifique-se que está na main
git checkout main
git pull origin main

# 2. Crie uma tag de versão
git tag -a v1.0.0 -m "Versão 1.0.0 - Primeiro Release"

# 3. Envie a tag para o GitHub
git push origin v1.0.0
```

O GitHub Actions vai automaticamente:
- ✅ Buildar para **Windows** (.exe)
- ✅ Buildar para **Linux** (.deb, .AppImage)
- ✅ Buildar para **macOS** (.dmg)
- ✅ Criar um **Release** com todos os arquivos

### 3️⃣ Verificar o Release

1. Vá em **Releases** no GitHub
2. Edite o release draft criado
3. Revise as notas de versão
4. Clique em **Publish release**

### 4️⃣ Testar a Landing Page

Após o push, acesse:
- **GitHub Pages:** `https://arkheioncorp.github.io/tiktrend-facil/`
- **Releases:** `https://github.com/arkheioncorp/tiktrend-facil/releases`

---

## 🖥️ Builds Multiplataforma

### Arquivos Gerados

| Plataforma | Arquivo | Descrição |
|------------|---------|-----------|
| **Windows** | `TikTrend-Finder_x64-setup.exe` | Instalador NSIS |
| **Windows** | `TikTrend-Finder_x64.msi` | Instalador MSI |
| **Linux** | `tiktrend-finder_amd64.deb` | Pacote Debian/Ubuntu |
| **Linux** | `TikTrend-Finder_amd64.AppImage` | Universal Linux |
| **macOS** | `TikTrend-Finder_x64.dmg` | Intel Macs |
| **macOS** | `TikTrend-Finder_aarch64.dmg` | Apple Silicon (M1/M2) |

### Requisitos para Build Local

```bash
# Windows
# - Visual Studio Build Tools 2019+
# - Node.js 20+
# - Rust 1.75+

# Linux
sudo apt install libwebkit2gtk-4.1-dev libgtk-3-dev libappindicator3-dev

# macOS
xcode-select --install
```

---

## 🌐 Domínio Personalizado (Opcional - Gratuito)

### Opção A: Usar domínio gratuito do GitHub
- URL: `https://arkheioncorp.github.io/tiktrend-facil/`

### Opção B: Domínio Personalizado + Cloudflare (Gratuito)

1. **Registrar domínio** (único custo: ~R$40/ano no registro.br)
2. **Usar Cloudflare** (gratuito) para DNS e CDN:

```
# Configurar DNS no Cloudflare:
CNAME  @    arkheioncorp.github.io
CNAME  www  arkheioncorp.github.io
```

3. No GitHub Pages, adicionar o domínio customizado

---

## 🔧 Comandos Úteis

### Build Local
```bash
# Desenvolvimento
npm run tauri:dev

# Build de produção
npm run tauri:build
```

### Criar Nova Versão
```bash
# Atualizar versão
npm version patch  # 1.0.0 -> 1.0.1
npm version minor  # 1.0.0 -> 1.1.0
npm version major  # 1.0.0 -> 2.0.0

# Push com tags
git push origin main --tags
```

---

## 📊 Checklist de Lançamento

### Antes do Lançamento
- [ ] Testar app em Windows, Linux e macOS
- [ ] Verificar todos os recursos funcionando
- [ ] Atualizar versão no `package.json` e `tauri.conf.json`
- [ ] Criar screenshots para a landing page
- [ ] Preparar notas de versão

### No Lançamento
- [ ] Criar tag de versão (`git tag v1.0.0`)
- [ ] Push da tag (`git push origin v1.0.0`)
- [ ] Aguardar builds completarem (~15-20 min)
- [ ] Publicar o release no GitHub
- [ ] Verificar landing page atualizada

### Pós-Lançamento
- [ ] Testar downloads em cada plataforma
- [ ] Anunciar nas redes sociais
- [ ] Monitorar issues no GitHub

---

## 💡 Dicas de Marketing (Grátis)

1. **Reddit**: Postar em r/dropshipping, r/tiktokshop
2. **Twitter/X**: Criar thread sobre o produto
3. **YouTube**: Vídeo demonstração
4. **TikTok**: Irônico, né? Fazer vídeo sobre o app
5. **Grupos Facebook**: Dropshipping, afiliados

---

## 🆘 Troubleshooting

### Build Falhou no GitHub Actions
- Verifique os logs em **Actions** > **workflow** > **job**
- Erros comuns: dependências faltando, secrets não configurados

### macOS não abre (Gatekeeper)
```bash
# Usuário deve executar:
xattr -cr /Applications/TikTrend\ Finder.app
```

### Linux AppImage não executa
```bash
chmod +x TikTrend-Finder_amd64.AppImage
./TikTrend-Finder_amd64.AppImage
```

---

## 📞 Suporte

- **Issues**: https://github.com/arkheioncorp/tiktrend-facil/issues
- **Discussions**: https://github.com/arkheioncorp/tiktrend-facil/discussions

---

**Versão:** 1.0.0  
**Atualizado:** 29 de Novembro de 2025
