# API de Checkout - TikTrend Finder

Documentação completa dos endpoints de pagamento e checkout.

## Base URL

```
Produção: https://api.arkheion-tiktrend.com.br
Desenvolvimento: http://localhost:8000
```

## Autenticação

Nenhuma autenticação é necessária para os endpoints de checkout. A licença é gerada após confirmação do pagamento.

---

## Endpoints

### 1. Criar Checkout

Cria uma sessão de pagamento.

```http
POST /checkout/create
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "João Silva",
  "email": "joao@email.com",
  "cpf": "12345678900",
  "phone": "11999999999",
  "payment_method": "pix",
  "product_id": "tiktrend_lifetime",
  "coupon": "LAUNCH10"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| name | string | ✅ | Nome completo (3-100 caracteres) |
| email | string | ✅ | Email válido |
| cpf | string | ✅ | CPF (11-14 caracteres) |
| phone | string | ❌ | Telefone |
| payment_method | string | ✅ | `pix`, `card` ou `boleto` |
| product_id | string | ❌ | ID do produto (default: `tiktrend_lifetime`) |
| coupon | string | ❌ | Código de cupom de desconto |

**Response (200 OK):**
```json
{
  "order_id": "TTF-20241201-ABC12345",
  "payment_url": "https://www.mercadopago.com.br/checkout/...",
  "pix_qr_code": "00020126580014br.gov.bcb.pix...",
  "pix_qr_code_base64": "data:image/png;base64,...",
  "pix_copy_paste": "00020126580014br.gov.bcb.pix...",
  "boleto_url": null,
  "boleto_barcode": null,
  "total": 47.40,
  "status": "pending",
  "expires_at": "2024-12-01T23:59:59Z"
}
```

---

### 2. Validar Cupom

Valida um código de cupom e retorna o desconto.

```http
POST /checkout/validate-coupon
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "LAUNCH10",
  "product_id": "tiktrend_lifetime"
}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "discount": 0.10,
  "final_price": 44.91,
  "message": "10% de desconto aplicado!"
}
```

---

### 3. Status do Pagamento

Consulta o status de um pagamento.

```http
GET /checkout/status/{order_id}
```

**Response (200 OK):**
```json
{
  "order_id": "TTF-20241201-ABC12345",
  "status": "approved",
  "payment_method": "pix",
  "license_key": "XXXX-XXXX-XXXX-XXXX",
  "download_url": "https://github.com/.../releases/latest"
}
```

**Status possíveis:**
- `pending`: Aguardando pagamento
- `approved`: Pagamento aprovado
- `rejected`: Pagamento recusado
- `cancelled`: Pagamento cancelado

---

### 4. Listar Produtos

Lista produtos disponíveis para compra.

```http
GET /checkout/products
```

**Response (200 OK):**
```json
{
  "products": [
    {
      "id": "tiktrend_lifetime",
      "name": "TikTrend Finder - Licença Vitalícia",
      "price": 49.90,
      "pix_discount": 0.05,
      "description": "Acesso vitalício ao TikTrend Finder"
    }
  ]
}
```

---

### 5. Callback de Sucesso (MercadoPago)

Recebe redirect do MercadoPago após pagamento aprovado.

```http
GET /checkout/success?collection_id=...&status=approved&external_reference=...
```

**Response (200 OK):**
```json
{
  "success": true,
  "order_id": "TTF-20241201-ABC12345",
  "license_key": "XXXX-XXXX-XXXX-XXXX",
  "redirect": "https://arkheion-tiktrend.com.br/pagamento/sucesso.html?..."
}
```

---

### 6. Callback de Falha (MercadoPago)

Recebe redirect do MercadoPago após pagamento recusado.

```http
GET /checkout/failure?collection_id=...&external_reference=...
```

**Response (200 OK):**
```json
{
  "success": false,
  "order_id": "TTF-20241201-ABC12345",
  "redirect": "https://arkheion-tiktrend.com.br/pagamento/falha.html?..."
}
```

---

### 7. Callback de Pendente (MercadoPago)

Recebe redirect do MercadoPago para pagamento pendente (boleto).

```http
GET /checkout/pending?collection_id=...&external_reference=...&payment_type=...
```

**Response (200 OK):**
```json
{
  "success": true,
  "status": "pending",
  "order_id": "TTF-20241201-ABC12345",
  "redirect": "https://arkheion-tiktrend.com.br/pagamento/pendente.html?..."
}
```

---

## Webhook MercadoPago

Os webhooks são recebidos em:

```http
POST /webhooks/mercadopago
```

**Headers requeridos:**
- `x-signature`: Assinatura HMAC do payload
- `x-request-id`: ID da requisição

**Eventos processados:**
- `payment.created`: Pagamento iniciado
- `payment.approved`: Pagamento aprovado → Ativa licença
- `payment.cancelled`: Pagamento cancelado
- `payment.refunded`: Reembolso processado → Desativa licença

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Dados inválidos |
| 401 | Assinatura de webhook inválida |
| 402 | Pagamento necessário |
| 404 | Pedido não encontrado |
| 500 | Erro interno do servidor |

---

## Cupons Disponíveis

| Código | Desconto | Validade |
|--------|----------|----------|
| LAUNCH10 | 10% | 31/01/2025 |
| BLACKFRIDAY | 20% | 30/11/2024 |

---

## Cálculo de Preço

1. Preço base: R$ 49,90
2. Se PIX: -5% (R$ 47,40)
3. Se cupom: desconto adicional aplicado sobre o valor com PIX

**Exemplo com PIX + LAUNCH10:**
- Base: R$ 49,90
- PIX -5%: R$ 47,40
- Cupom -10%: R$ 42,66

---

## Variáveis de Ambiente

Configure no backend:

```env
# MercadoPago
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-...
MERCADO_PAGO_PUBLIC_KEY=APP_USR-...
MERCADO_PAGO_WEBHOOK_SECRET=...

# URLs
API_URL=https://api.arkheion-tiktrend.com.br
FRONTEND_URL=https://arkheion-tiktrend.com.br
```

---

## Fluxo de Pagamento

```
1. Cliente acessa /checkout.html
2. Preenche dados e escolhe método
3. Frontend POST /checkout/create
4. Backend cria preferência no MercadoPago
5. Cliente paga (PIX QR, boleto, cartão)
6. MercadoPago envia webhook para /webhooks/mercadopago
7. Backend valida e ativa licença
8. Cliente recebe email com chave de licença
9. Redirect para /pagamento/sucesso.html
```

---

## SDKs e Integrações

### JavaScript (Frontend)

```javascript
// Criar checkout
const response = await fetch('/checkout/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'João Silva',
    email: 'joao@email.com',
    cpf: '12345678900',
    payment_method: 'pix'
  })
});

const { order_id, pix_copy_paste } = await response.json();
```

### Python (Backend)

```python
from api.services.mercadopago import MercadoPagoService

mp = MercadoPagoService()
pix_data = await mp.create_pix_payment(
    amount=49.90,
    email="cliente@email.com",
    cpf="12345678900",
    name="Cliente",
    external_reference="ORDER-123"
)
```

---

**Última atualização:** Dezembro 2024
