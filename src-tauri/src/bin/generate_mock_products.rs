// Mock Product Generator
// Generates realistic Brazilian TikTok Shop products

use rand::Rng;
use uuid::Uuid;

fn main() {
    println!("Generating realistic Brazilian TikTok Shop products...\n");
    
    let products = generate_products(100);
    
    println!("-- Generated {} products", products.len());
    println!("-- Copy and paste into sqlite3\n");
    println!("BEGIN TRANSACTION;");
    
    for product in &products {
        println!("{}", product);
    }
    
    println!("COMMIT;");
    println!("\n-- Done! {} products generated.", products.len());
}

fn generate_products(count: usize) -> Vec<String> {
    let mut rng = rand::thread_rng();
    let mut products = Vec::new();
    
    let categories = vec![
        ("Beleza & Skincare", get_beauty_products()),
        ("Eletrônicos", get_electronics_products()),
        ("Casa & Decorações", get_home_products()),
        ("Moda & Acessórios", get_fashion_products()),
        ("Saúde & Fitness", get_health_products()),
    ];
    
    let mut id_counter = 2000;
    
    for i in 0..count {
        let category_idx = i % categories.len();
        let (category, items) = &categories[category_idx];
        let item_idx = rng.gen_range(0..items.len());
        let item = &items[item_idx];
        
        id_counter += 1;
        let uuid = Uuid::new_v4().to_string();
        let tiktok_id = id_counter.to_string();
        
        let base_price: f64 = rng.gen_range(29.90..499.90);
        let price = (base_price * 10.0_f64).round() / 10.0_f64;
        let original_price: Option<f64> = if rng.gen_bool(0.3) {
            Some((price * rng.gen_range(1.2_f64..1.8_f64) * 10.0_f64).round() / 10.0_f64)
        } else {
            None
        };
        
        let sales_count = rng.gen_range(50..5000);
        let reviews = rng.gen_range(10..(sales_count / 5).max(10));
        let rating = rng.gen_range(42..50) as f64 / 10.0;
        
        let image_colors = ["ff69b4", "9370db", "4169e1", "00ced1", "ff6347", "ffa500", "32cd32", "ff1493"];
        let color = image_colors[rng.gen_range(0..image_colors.len())];
        let image_text = item.replace(" ", "+");
        
        let is_on_sale = original_price.is_some();
        let has_free_shipping = rng.gen_bool(0.4);
        let is_trending = rng.gen_bool(0.2);
        
        let sql = format!(
            "INSERT INTO products (id, tiktok_id, title, price, original_price, currency, category, product_rating, reviews_count, sales_count, image_url, product_url, is_on_sale, has_free_shipping, is_trending, in_stock, collected_at, updated_at) VALUES ('{}', '{}', '{}', {:.2}, {}, 'BRL', '{}', {:.1}, {}, {}, 'https://placehold.co/400x400/{}/white?text={}', 'https://www.tiktok.com/product/{}', {}, {}, {}, 1, datetime('now'), datetime('now'));",
            uuid,
            tiktok_id,
            item,
            price,
            original_price.map_or("NULL".to_string(), |p| format!("{:.2}", p)),
            category,
            rating,
            reviews,
            sales_count,
            color,
            image_text,
            tiktok_id,
            if is_on_sale { 1 } else { 0 },
            if has_free_shipping { 1 } else { 0 },
            if is_trending { 1 } else { 0 }
        );
        
        products.push(sql);
    }
    
    products
}

fn get_beauty_products() -> Vec<&'static str> {
    vec![
        "Kit Maquiagem Profissional 32 Peças com Estojo",
        "Paleta de Sombras 120 Cores Matte e Glitter",
        "Base Líquida Alta Cobertura FPS 30",
        "Máscara de Cílios Volume 10x à Prova D'água",
        "Batom Líquido Matte 12h Longa Duração",
        "Escova Alisadora Elétrica Cerâmica Profissional",
        "Secador de Cabelo Íons Negativos 2000W",
        "Chapinha Titanium Bivolt Profissional 450F",
        "Creme Anti-Rugas Vitamina C + Ácido Hialurônico",
        "Sérum Facial Clareador Manchas 30ml",
        "Máscara Capilar Hidratação Profunda 1kg",
        "Kit Pincéis Maquiagem Profissional 12 Peças",
        "Delineador Líquido à Prova D'água Preto",
        "Pó Compacto Matte Alta Fixação",
        "Primer Facial Poros Invisíveis",
    ]
}

fn get_electronics_products() -> Vec<&'static str> {
    vec![
        "Smartwatch Fitness Tracker Bluetooth 5.0",
        "Fone Bluetooth sem Fio TWS Cancelamento Ruído",
        "Carregador Rápido USB-C 65W 3 Portas",
        "Power Bank 20000mAh Carregamento Rápido",
        "Caixa de Som Bluetooth Portátil 50W",
        "Smart TV LED 43' 4K Android Wi-Fi",
        "Câmera de Segurança Wi-Fi 360° Visão Noturna",
        "Lâmpada LED Inteligente RGB Alexa/Google",
        "Tablet 10' 128GB Wi-Fi Android 12",
        "Teclado Mecânico Gamer RGB Switch Blue",
        "Mouse Gamer RGB 12000 DPI Programável",
        "Webcam Full HD 1080p Microfone Embutido",
        "Ring Light 26cm Tripé 2m Controle Bluetooth",
        "SSD Externo 1TB USB 3.2 Portátil",
        "Controle Joystick Sem Fio Bluetooth PC/Mobile",
    ]
}

fn get_home_products() -> Vec<&'static str> {
    vec![
        "Jogo de Panelas Antiaderente 7 Peças Cerâmica",
        "Conjunto Facas Cozinha Inox 8 Peças Afiadas",
        "Liquidificador Turbo 1200W 12 Velocidades",
        "Air Fryer Digital 5L 1500W Preta",
        "Cafeteira Elétrica Programável 1.8L",
        "Jogo de Cama Queen 4 Peças 100% Algodão",
        "Edredom King Size Dupla Face Microfibra",
        "Tapete Sala Grande 2x1.5m Antiderrapante",
        "Aspirador Robô Inteligente Wi-Fi Mapeamento",
        "Ventilador de Torre Silencioso Controle Remoto",
        "Purificador de Ar HEPA Ionizador UV",
        "Umidificador de Ar Ultrassônico LED 7 Cores",
        "Organizador Multiuso 6 Gavetas Plástico",
        "Estante Livros 5 Prateleiras MDF Branco",
        "Quadro Decorativo Canvas 3 Peças Abstrato",
    ]
}

fn get_fashion_products() -> Vec<&'static str> {
    vec![
        "Tênis Esportivo Feminino Academia Corrida",
        "Bolsa Feminina Transversal Couro Sintético",
        "Relógio Digital Esportivo à Prova D'água",
        "Óculos de Sol Polarizado UV400 Unissex",
        "Carteira Masculina Couro Legítimo RFID",
        "Cinto Couro Masculino Fivela Automática",
        "Mochila Notebook 15.6' Impermeável USB",
        "Chinelo Slide Confortável Anatômico",
        "Conjunto Moletom Feminino Inverno Peluciado",
        "Jaqueta Corta-Vento Masculina Impermeável",
        "Legging Fitness Cintura Alta Sem Costura",
        "Camisa Polo Masculina Algodão Básica",
        "Vestido Feminino Midi Manga Longa Casual",
        "Short Jeans Feminino Cintura Alta Destroyed",
        "Bota Coturno Feminino Plataforma Tratorada",
    ]
}

fn get_health_products() -> Vec<&'static str> {
    vec![
        "Colchonete Yoga EVA 10mm Antiderrapante",
        "Kit Halteres 2kg + 3kg + 5kg Emborrachado",
        "Faixa Elástica Exercícios Kit 5 Resistências",
        "Corda Pular Profissional Rolamento Ajustável",
        "Garrafa Térmica 1L Inox Mantém 24h Gelado",
        "Suplemento Whey Protein 900g Chocolate",
        "Creatina Monohidratada 300g Pura Micronizada",
        "Termogênico Cafeína 60 Cápsulas Original",
        "Ômega 3 1000mg 120 Cápsulas Importado",
        "Vitamina D3 2000UI 60 Cápsulas",
        "Balança Digital Bioimpedância Bluetooth App",
        "Massageador Pistola Muscular 6 Velocidades",
        "Rolo Massagem Miofascial Texturizado 33cm",
        "Esteira Ergométrica Dobrável 10km/h Display LCD",
        "Bicicleta Ergométrica Residencial 8kg",
    ]
}
