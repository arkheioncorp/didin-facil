# 🎯 Como Usar o TikTrend Finder

## 📊 Status Atual

✅ **Database populado** com 6 produtos de exemplo para teste  
✅ **Busca funcionando** - você pode buscar produtos agora  
⚠️ **Scraping** - precisa configurar URL correta do TikTok Shop

---

## 🔍 BUSCAR Produtos (Search)

### O que faz:
Procura produtos **já salvos no database local**

### Como usar:
1. Digite termo de busca (ex: "Casa Inteligente", "Maquiagem")
2. Use filtros de categoria se quiser
3. Clique em **"Buscar"**
4. ✅ Agora vai funcionar pois o DB tem produtos!

### Produtos de exemplo inseridos:
- 🎨 **Conjunto de Maquiagem Profissional** - R$ 129,90
- 💇 **Escova Alisadora Elétrica** - R$ 89,90
- 🏠 **Kit Casa Inteligente Alexa** - R$ 299,90
- ⌚ **Smartwatch Fitness Tracker** - R$ 149,90
- 🍳 **Jogo de Panelas Antiaderente** - R$ 179,90
- 💡 **Luminária LED RGB** - R$ 59,90

---

## 🕷️ SCRAPING (Buscar Novos Produtos)

### O que faz:
Busca produtos **novos do TikTok Shop** e salva no database

### ⚠️ IMPORTANTE - URLs do TikTok Shop:

As URLs oficiais `shop.tiktok.com` retornam 404. Você tem 3 opções:

#### Opção 1: Usar Fixture de Teste (RECOMENDADO para validar funcionalidade)
```
file:///home/jhonslife/Didin Facil/src-tauri/tests/fixtures/tiktok_shop.html
```

#### Opção 2: Descobrir URL Correta
1. Abra o TikTok no navegador normal
2. Navegue até TikTok Shop
3. Copie a URL que funciona
4. Use essa URL no scraper

#### Opção 3: Verificar Região
- TikTok Shop BR: `https://www.tiktok.com/@shop` (pode variar)
- TikTok Shop US: Diferentes domínios por região

### Como iniciar o scraping:

**Via Console do Browser (F12):**
```javascript
window.__TAURI__.core.invoke("scrape_tiktok_shop", { 
  config: { 
    max_products: 10,
    categories: ["file:///home/jhonslife/Didin Facil/src-tauri/tests/fixtures/tiktok_shop.html"],
    use_proxy: false,
    proxy_list: []
  }
}).then(r => console.log("✅ Scraping iniciado!", r))
  .catch(e => console.error("❌ Erro:", e))
```

**Ou via UI:**
- Procure botão "Iniciar Scraping" ou similar
- Configure as categorias/quantidade
- Clique para iniciar

---

## 📝 Monitorar Scraping

### Ver logs em tempo real:
```bash
tail -f /tmp/tauri-live.log | grep -E "(Starting|Parsed|Error)"
```

### O que você verá:
```
[INFO] Starting TikTok Shop scraper...
[INFO] Starting browser (headless: true)...
[DEBUG] Injected stealth scripts  
[INFO] Navigating to: [URL]
[INFO] Parsed 3 products total
[INFO] Scraping completed: 3 products found
```

---

## 🧪 Testar Agora

1. **Recarregue a página** do app (Ctrl+R)
2. **Busque "Casa"** - deve encontrar o Kit Casa Inteligente
3. **Busque "Maquiagem"** - deve encontrar o Conjunto de Maquiagem
4. ✅ **Search funcionando!**

Para fazer scraping real, você precisa descobrir a URL correta do TikTok Shop na sua região.

---

**Pronto para testar! 🚀**
