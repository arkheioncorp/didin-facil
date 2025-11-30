# Política de Segurança - TikTrend Finder

## Versões Suportadas

Atualmente, fornecemos atualizações de segurança para as seguintes versões:

| Versão | Suportada          |
| ------ | ------------------ |
| 1.x.x  | :white_check_mark: |
| < 1.0  | :x:                |

## Reportando uma Vulnerabilidade

A segurança do TikTrend Finder é levada muito a sério. Agradecemos sua ajuda em divulgar vulnerabilidades de forma responsável.

### Como Reportar

**NÃO reporte vulnerabilidades de segurança através de issues públicas do GitHub.**

Em vez disso, envie um e-mail para: **security@arkheioncorp.com**

### O Que Incluir no Relatório

Por favor, inclua o máximo de informações possível:

1. **Tipo de vulnerabilidade** (ex: XSS, SQL Injection, RCE)
2. **Componente afetado** (ex: API, Frontend, Desktop App)
3. **Passos para reproduzir**
   - Passos detalhados para reproduzir a vulnerabilidade
   - Código de prova de conceito (se aplicável)
   - Screenshots ou vídeos (se aplicável)
4. **Impacto potencial**
   - O que um atacante poderia fazer?
   - Quais dados poderiam ser expostos?
5. **Versão afetada**
6. **Ambiente** (sistema operacional, navegador, etc.)
7. **Sugestões de correção** (opcional)

### Processo de Resposta

1. **Confirmação:** Confirmaremos o recebimento em até 48 horas
2. **Triagem:** Avaliaremos a vulnerabilidade em até 7 dias
3. **Comunicação:** Manteremos você informado sobre o progresso
4. **Correção:** Desenvolveremos e testaremos a correção
5. **Divulgação:** Coordenaremos a divulgação pública com você

### Linha do Tempo

| Etapa | Prazo |
|-------|-------|
| Confirmação de recebimento | 48 horas |
| Avaliação inicial | 7 dias |
| Plano de correção | 14 dias |
| Patch disponível | 30-90 dias* |

*Dependendo da complexidade e severidade

### Recompensas (Bug Bounty)

Atualmente, não oferecemos programa formal de bug bounty com recompensas monetárias. No entanto, reconhecemos publicamente pesquisadores de segurança que reportam vulnerabilidades válidas (com sua permissão).

### Hall da Fama

Pesquisadores que reportaram vulnerabilidades válidas:

*Esta lista será atualizada conforme vulnerabilidades forem reportadas e corrigidas.*

## Política de Divulgação

### Divulgação Coordenada

Seguimos o modelo de divulgação coordenada:

1. Você reporta a vulnerabilidade para nós
2. Trabalhamos juntos para corrigir
3. Lançamos a correção
4. Você pode divulgar publicamente após o patch

### Prazo de Divulgação

- Vulnerabilidades **críticas:** 90 dias
- Vulnerabilidades **altas:** 90 dias
- Vulnerabilidades **médias:** 120 dias
- Vulnerabilidades **baixas:** 180 dias

Se não corrigirmos no prazo, você pode divulgar publicamente.

## Escopo

### Em Escopo

- Aplicativo desktop TikTrend Finder
- API backend (api.arkheioncorp.com)
- Website principal (arkheioncorp.com)
- Integrações OAuth
- Processamento de pagamentos (coordenado com MercadoPago)

### Fora do Escopo

- Vulnerabilidades em dependências de terceiros (reporte ao mantenedor)
- Engenharia social contra funcionários
- Ataques físicos
- Ataques de negação de serviço (DoS/DDoS)
- Spam ou abuso de conta
- Vulnerabilidades em serviços de terceiros integrados (TikTok, Instagram, etc.)

### Testes Não Permitidos

- Testes contra sistemas de produção sem autorização
- Acesso ou modificação de dados de outros usuários
- Interrupção de serviços
- Exfiltração de dados em massa
- Testes de engenharia social

## Medidas de Segurança

### Práticas de Desenvolvimento

- Code review obrigatório para todas as mudanças
- Análise estática de código (CodeQL, Semgrep)
- Testes de segurança automatizados
- Dependências auditadas regularmente
- Secrets gerenciados via variáveis de ambiente seguras

### Infraestrutura

- HTTPS/TLS 1.3 obrigatório
- Firewalls e WAF (Cloudflare)
- Monitoramento de intrusão
- Backups criptografados
- Logs de auditoria

### Dados

- Criptografia em repouso (AES-256)
- Criptografia em trânsito (TLS)
- Hashing de senhas (bcrypt)
- Tokens de curta duração (JWT)
- Princípio do menor privilégio

## Contato

- **E-mail de segurança:** security@arkheioncorp.com
- **PGP Key:** [Link para chave PGP]
- **Chave SHA256 Fingerprint:** [Fingerprint]

## Atualizações desta Política

Esta política pode ser atualizada periodicamente. Mudanças significativas serão comunicadas através de:

- E-mail para usuários registrados
- Aviso no website
- Changelog do repositório

---

*Última atualização: 30 de novembro de 2025*

*© 2025 Arkheioncorp. Todos os direitos reservados.*
