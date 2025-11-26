// 🔍 DEBUG SCRIPT - Testar Scraper Manualmente
// Cole este código no Console do Browser (F12 → Console)

// Importar o invoke do Tauri
const { invoke } = window.__TAURI__.core;

// Teste 1: Verificar se o comando está registrado
console.log("🧪 Teste 1: Verificando comandos disponíveis...");
console.log("Tauri disponível:", !!window.__TAURI__);
console.log("invoke disponível:", !!invoke);

// Teste 2: Invocar scraper com configuração mínima
console.log("\n🧪 Teste 2: Invocando scraper...");

const testConfig = {
    max_products: 5,
    categories: ["file:///home/jhonslife/Didin Facil/src-tauri/tests/fixtures/tiktok_shop.html"],
    use_proxy: false,
    proxy_list: []
};

invoke("scrape_tiktok_shop", { config: testConfig })
    .then(result => {
        console.log("✅ Scraper iniciado com sucesso!");
        console.log("Resultado:", result);
    })
    .catch(error => {
        console.error("❌ Erro ao iniciar scraper:");
        console.error(error);

        // Detalhes do erro
        if (error.message) console.error("Mensagem:", error.message);
        if (error.code) console.error("Código:", error.code);
    });

// Teste 3: Verificar status
setTimeout(() => {
    console.log("\n🧪 Teste 3: Verificando status...");
    invoke("get_scraper_status")
        .then(status => {
            console.log("Status atual:", status);
        })
        .catch(error => {
            console.error("Erro ao obter status:", error);
        });
}, 2000);

console.log("\n📊 Aguardando resposta do scraper...");
console.log("💡 Verifique também os logs em: /tmp/tauri-live.log");
