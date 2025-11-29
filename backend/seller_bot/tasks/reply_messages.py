# ============================================
# Reply Messages Task - Resposta a Mensagens
# ============================================

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Tipos de mensagens"""
    BUYER_QUESTION = "buyer_question"      # Pergunta de comprador
    ORDER_INQUIRY = "order_inquiry"        # Dúvida sobre pedido
    COMPLAINT = "complaint"                # Reclamação
    GENERAL = "general"                    # Mensagem geral


class AutoReplyConfig(BaseModel):
    """Configuração de respostas automáticas"""
    
    # Templates de resposta por tipo
    templates: dict[str, str] = Field(
        default={
            "greeting": "Olá! Obrigado por entrar em contato. Como posso ajudar?",
            "order_status": "Seu pedido está sendo processado. O código de rastreio será enviado assim que disponível.",
            "shipping_time": "O prazo de entrega é de 5 a 15 dias úteis após o envio.",
            "product_question": "Fico feliz em ajudar! Poderia especificar sua dúvida sobre o produto?",
            "thanks": "Agradecemos a preferência! Qualquer dúvida, estamos à disposição.",
        }
    )
    
    # Usar IA para personalizar respostas
    use_ai_response: bool = Field(
        default=True,
        description="Usar LLM para gerar respostas contextualizadas"
    )
    
    # Limite de mensagens por execução
    max_messages: int = Field(
        default=20,
        description="Máximo de mensagens a responder por execução"
    )


class ReplyMessagesTask:
    """
    Tarefa para responder mensagens de compradores.
    
    Fluxos:
    - Listar mensagens não lidas
    - Responder automaticamente usando templates
    - Gerar respostas contextualizadas com IA
    """
    
    TASK_TYPE = "reply_messages"
    
    @staticmethod
    def build_list_messages_prompt() -> str:
        """Prompt para listar mensagens pendentes"""
        
        return """
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é listar todas as mensagens não lidas dos compradores.

INSTRUÇÕES:
1. Clique em "Mensagens do comprador" no canto superior direito
2. Verifique o número de mensagens não lidas
3. Para cada conversa com mensagens novas:
   a. Clique na conversa
   b. Leia a última mensagem do comprador
   c. Anote: nome do comprador, assunto, e se está relacionado a algum pedido
4. Retorne a lista de mensagens pendentes

FORMATO DE RETORNO:
Para cada mensagem, informe:
- Comprador: [nome]
- Assunto: [resumo]
- Pedido relacionado: [ID se houver]
- Urgência: [alta/média/baixa]
"""
    
    @staticmethod
    def build_reply_prompt(
        config: Optional[AutoReplyConfig] = None,
        specific_buyer: Optional[str] = None,
    ) -> str:
        """Prompt para responder mensagens"""
        
        config = config or AutoReplyConfig()
        
        buyer_filter = f"\nRESPONDER APENAS: {specific_buyer}" if specific_buyer else ""
        
        templates_text = "\n".join(
            f"- {key}: \"{value}\""
            for key, value in config.templates.items()
        )
        
        ai_instruction = """
PARA CADA MENSAGEM:
- Leia o contexto da conversa
- Identifique o tipo de pergunta (produto, pedido, entrega, etc.)
- Gere uma resposta personalizada e educada
- Se não souber responder, use: "Vou verificar essa informação e retorno em breve."
""" if config.use_ai_response else f"""
TEMPLATES DISPONÍVEIS:
{templates_text}

Use o template mais apropriado para cada situação.
"""
        
        return f"""
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é responder mensagens de compradores.
{buyer_filter}

LIMITE: Responder até {config.max_messages} mensagens

INSTRUÇÕES:
1. Clique em "Mensagens do comprador"
2. Identifique conversas com mensagens não lidas
3. Para cada conversa:
   a. Abra a conversa
   b. Leia as mensagens do comprador
   {ai_instruction}
   c. Digite a resposta no campo de texto
   d. Clique em enviar
4. Registre quantas mensagens foram respondidas

IMPORTANTE:
- Seja educado e profissional
- Não prometa prazos que não pode cumprir
- Se for reclamação grave, apenas responda que vai verificar
- Nunca compartilhe dados sensíveis

CONTAGEM:
- Mensagens respondidas: [número]
- Mensagens que precisam de atenção manual: [número]
"""
    
    @staticmethod
    def build_check_reviews_prompt() -> str:
        """Prompt para verificar e responder avaliações"""
        
        return """
Você está na Central do Vendedor do TikTok Shop.
Sua tarefa é verificar e responder às avaliações de produtos.

INSTRUÇÕES:
1. Use a barra de pesquisa e busque por "avaliações" (Ctrl+K)
2. Ou navegue até a seção de avaliações de produtos
3. Filtre por avaliações não respondidas
4. Para cada avaliação:
   a. Leia o comentário do cliente
   b. Verifique a nota (estrelas)
   c. Se for avaliação positiva (4-5 estrelas):
      - Agradeça pela avaliação
      - Exemplo: "Obrigado pela avaliação! Ficamos felizes que gostou!"
   d. Se for avaliação negativa (1-3 estrelas):
      - Peça desculpas pelo inconveniente
      - Ofereça ajuda
      - Exemplo: "Lamentamos pelo ocorrido. Entre em contato conosco para resolvermos."
   e. Clique em responder e envie

IMPORTANTE:
- Personalize as respostas quando possível
- Não seja genérico demais
- Avaliações negativas merecem atenção especial
"""
