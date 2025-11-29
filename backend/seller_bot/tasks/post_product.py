# ============================================
# Post Product Task - Publicação de Produtos
# ============================================

from typing import Optional
from pydantic import BaseModel, Field


class ProductData(BaseModel):
    """Dados do produto para publicação"""
    
    # Informações básicas
    title: str = Field(..., description="Título do produto")
    description: str = Field(..., description="Descrição completa")
    category: str = Field(..., description="Categoria do produto")
    
    # Preços
    price: float = Field(..., description="Preço de venda")
    original_price: Optional[float] = Field(None, description="Preço original (riscado)")
    
    # Estoque
    stock: int = Field(default=100, description="Quantidade em estoque")
    sku: Optional[str] = Field(None, description="SKU do produto")
    
    # Imagens (paths locais ou URLs)
    images: list[str] = Field(..., description="Lista de imagens do produto")
    
    # Dimensões e peso
    weight_kg: Optional[float] = Field(None, description="Peso em kg")
    length_cm: Optional[float] = Field(None, description="Comprimento em cm")
    width_cm: Optional[float] = Field(None, description="Largura em cm")
    height_cm: Optional[float] = Field(None, description="Altura em cm")
    
    # Variantes (tamanho, cor, etc.)
    variants: Optional[list[dict]] = Field(None, description="Variantes do produto")


class PostProductTask:
    """
    Tarefa para publicar um produto no TikTok Shop.
    
    Fluxo:
    1. Navegar para Produtos > Adicionar novo produto
    2. Preencher formulário com dados do produto
    3. Upload de imagens
    4. Selecionar categoria
    5. Configurar preço e estoque
    6. Publicar
    """
    
    TASK_TYPE = "post_product"
    
    @staticmethod
    def build_prompt(product: ProductData) -> str:
        """
        Constrói o prompt de linguagem natural para o browser-use.
        
        O agente vai "entender" essa descrição e executar as ações
        necessárias no navegador para completar a tarefa.
        """
        
        prompt = f"""
Você está na Central do Vendedor do TikTok Shop (seller-br.tiktok.com).
Sua tarefa é publicar um novo produto com as seguintes informações:

PRODUTO:
- Título: {product.title}
- Categoria: {product.category}
- Preço: R$ {product.price:.2f}
{"- Preço Original: R$ " + f"{product.original_price:.2f}" if product.original_price else ""}
- Estoque: {product.stock} unidades
{"- SKU: " + product.sku if product.sku else ""}

DESCRIÇÃO:
{product.description}

IMAGENS:
{chr(10).join(f"- {img}" for img in product.images)}

{"DIMENSÕES:" if product.weight_kg else ""}
{"- Peso: " + f"{product.weight_kg} kg" if product.weight_kg else ""}
{"- Dimensões: " + f"{product.length_cm}x{product.width_cm}x{product.height_cm} cm" if product.length_cm else ""}

INSTRUÇÕES:
1. No menu lateral, clique em "Produtos"
2. Clique em "Adicionar novo produto"
3. Faça upload das imagens do produto
4. Preencha o título exatamente como especificado
5. Selecione a categoria correta (busque por "{product.category}")
6. Preencha a descrição completa
7. Configure o preço e estoque
8. Se houver campos de peso/dimensões, preencha-os
9. Revise todas as informações
10. Clique em "Publicar" ou "Enviar para revisão"

IMPORTANTE:
- Aguarde cada página carregar completamente antes de interagir
- Se aparecer popup ou modal, feche-o antes de continuar
- Confirme se o produto foi publicado com sucesso
"""
        return prompt.strip()
    
    @staticmethod
    def build_batch_prompt(products: list[ProductData]) -> str:
        """
        Constrói prompt para publicação em lote.
        """
        prompts = []
        for i, product in enumerate(products, 1):
            prompts.append(f"=== PRODUTO {i} de {len(products)} ===")
            prompts.append(PostProductTask.build_prompt(product))
            prompts.append("\nApós publicar este produto, prossiga para o próximo.\n")
        
        return "\n".join(prompts)
