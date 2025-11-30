# 🌐 Configuração do Domínio arkheion-tiktrend.com.br

## Configuração de DNS

Adicione os seguintes registros DNS no seu provedor (registro.br, Cloudflare, etc.):

### Opção 1: Usando CNAME (Recomendado)

| Tipo | Nome | Valor | TTL |
|------|------|-------|-----|
| CNAME | @ | arkheioncorp.github.io | 3600 |
| CNAME | www | arkheioncorp.github.io | 3600 |

> ⚠️ Alguns provedores não permitem CNAME na raiz (@). Use a Opção 2 nesse caso.

### Opção 2: Usando registros A (se CNAME na raiz não funcionar)

| Tipo | Nome | Valor | TTL |
|------|------|-------|-----|
| A | @ | 185.199.108.153 | 3600 |
| A | @ | 185.199.109.153 | 3600 |
| A | @ | 185.199.110.153 | 3600 |
| A | @ | 185.199.111.153 | 3600 |
| CNAME | www | arkheioncorp.github.io | 3600 |

---

## Configuração no GitHub

1. Vá em **Settings** do repositório
2. Clique em **Pages**
3. Em **Custom domain**, digite: `arkheion-tiktrend.com.br`
4. Clique em **Save**
5. Marque **Enforce HTTPS** (após DNS propagar)

---

## Verificação

Após configurar, aguarde de 10 minutos a 24 horas para propagação DNS.

Verifique com:
```bash
# Verificar registros A
dig arkheion-tiktrend.com.br +short

# Verificar se está apontando corretamente
curl -I https://arkheion-tiktrend.com.br
```

---

## URLs Finais

| URL | Descrição |
|-----|-----------|
| https://arkheion-tiktrend.com.br | Landing page principal |
| https://arkheion-tiktrend.com.br/download.html | Redireciona para releases |
| https://www.arkheion-tiktrend.com.br | Redireciona para principal |

---

## Cloudflare (Opcional, Gratuito)

Para melhor performance e SSL gratuito:

1. Crie conta em [cloudflare.com](https://cloudflare.com)
2. Adicione o domínio `arkheion-tiktrend.com.br`
3. Atualize os nameservers no registro.br
4. Configure os registros DNS no painel do Cloudflare

### Vantagens do Cloudflare:
- ✅ CDN global (site mais rápido)
- ✅ SSL/HTTPS automático
- ✅ Proteção DDoS
- ✅ Analytics gratuitos
- ✅ Cache automático
