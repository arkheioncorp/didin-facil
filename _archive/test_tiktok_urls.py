#!/usr/bin/env python3
"""
Script para testar URLs do TikTok Shop e verificar onde encontrar produtos
"""

import asyncio
from playwright.async_api import async_playwright

async def check_tiktok_urls():
    urls_to_test = [
        'https://shop.tiktok.com',
        'https://shop.tiktok.com/browse',
        'https://shop.tiktok.com/search?keyword=beauty',
        'https://www.tiktok.com/business/en',
        'https://affiliate.tiktok.com',
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        for url in urls_to_test:
            print(f'\n🔍 Testando: {url}')
            print('=' * 80)
            
            page = await context.new_page()
            
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                print(f'Status: {response.status}')
                print(f'URL Final: {page.url}')
                print(f'Title: {await page.title()}')
                
                # Esperar um pouco para carregar
                await page.wait_for_timeout(3000)
                
                # Tentar encontrar produtos
                product_selectors = [
                    '[data-e2e="product-card"]',
                    '.product-card',
                    '[class*="product"]',
                    '[data-testid*="product"]',
                    'a[href*="/product/"]',
                ]
                
                found_products = False
                for selector in product_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f'✅ Encontrado {len(elements)} elementos com: {selector}')
                            found_products = True
                            
                            # Mostrar alguns exemplos
                            for i, el in enumerate(elements[:3]):
                                try:
                                    text = await el.text_content()
                                    href = await el.get_attribute('href')
                                    print(f'  [{i+1}] Texto: {text[:100] if text else "N/A"}')
                                    print(f'      Link: {href}')
                                except:
                                    pass
                            break
                    except:
                        pass
                
                if not found_products:
                    print('❌ Nenhum produto encontrado com os seletores conhecidos')
                    
                    # Tentar ver o conteúdo da página
                    body_text = await page.text_content('body')
                    print(f'\n📄 Primeiros 500 caracteres do body:')
                    print(body_text[:500] if body_text else 'Vazio')
                    
                # Tirar screenshot
                screenshot_name = f'debug_{url.replace("https://", "").replace("/", "_").replace("?", "_").replace("=", "_")}.png'
                await page.screenshot(path=screenshot_name, full_page=False)
                print(f'📸 Screenshot salvo: {screenshot_name}')
                
            except Exception as e:
                print(f'❌ Erro ao acessar: {str(e)}')
            
            finally:
                await page.close()
            
            # Pausa entre requisições
            await asyncio.sleep(2)
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check_tiktok_urls())
