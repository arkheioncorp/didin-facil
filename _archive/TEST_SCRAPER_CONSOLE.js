// Test scraper via console
// Run in browser console (F12)
const { invoke } = window.__TAURI__.core;

console.log("🧪 Iniciando teste de scraping...");

const config = {
    max_products: 10,
    categories: ["file:///home/jhonslife/Didin Facil/src-tauri/tests/fixtures/tiktok_shop.html"],
    use_proxy: false
};

invoke("scrape_tiktok_shop", { config })
    .then(result => {
        console.log("✅ SCRAPING INICIADO!");
        console.log("Status:", result);

        // Monitor status
        const interval = setInterval(async () => {
            const status = await invoke("get_scraper_status");
            console.log("📊 Status:", status);

            if (!status.is_running) {
                console.log("✅ Scraping finalizado!");
                console.log(`Total de produtos: ${status.products_found}`);
                clearInterval(interval);
            }
        }, 2000);
    })
    .catch(error => {
        console.error("❌ ERRO:", error);
    });

console.log("⏳ Aguardando início do scraping...");
console.log("💡 Monitore os logs em /tmp/tauri-final.log");
