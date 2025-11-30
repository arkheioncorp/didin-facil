/**
 * Privacy Policy Page
 * Página pública para Política de Privacidade - Versão Completa LGPD
 */

import * as React from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TikTrendIcon } from "@/components/icons";
import { Footer } from "@/components/layout/Footer";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export const Privacy: React.FC = () => {
  const lastUpdated = "30 de novembro de 2025";

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-tiktrend-primary/5">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <TikTrendIcon size={32} />
            <span className="font-bold text-xl bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary bg-clip-text text-transparent">
              TikTrend Finder
            </span>
          </Link>
          <Link to="/login">
            <Button variant="outline">Entrar</Button>
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="mb-8">
          <CardContent className="p-8">
            <div className="mb-8">
              <h1 className="text-3xl font-bold mb-2">🔒 Política de Privacidade</h1>
              <p className="text-muted-foreground">
                Última atualização: {lastUpdated}
              </p>
            </div>

            {/* Badge LGPD */}
            <div className="p-4 mb-8 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900 rounded-lg flex items-center gap-3">
              <span className="text-2xl">🇧🇷</span>
              <div>
                <p className="font-medium text-green-700 dark:text-green-400">
                  Conformidade com a LGPD
                </p>
                <p className="text-sm text-green-600 dark:text-green-500">
                  Esta política está em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
                </p>
              </div>
            </div>

            <div className="prose prose-slate dark:prose-invert max-w-none">
              <Accordion type="multiple" className="w-full space-y-4">
                
                {/* Seção 1 - Introdução */}
                <AccordionItem value="section-1" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    1. Introdução e Controlador
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <p>
                      A Arkheioncorp ("nós", "nosso", "Empresa"), operadora do TikTrend Finder, 
                      está comprometida com a proteção da sua privacidade. Esta Política descreve 
                      como coletamos, usamos, armazenamos e protegemos seus dados pessoais.
                    </p>
                    <div className="p-4 bg-muted/50 rounded-lg">
                      <h4 className="font-medium text-foreground mb-2">Controlador de Dados</h4>
                      <p className="text-sm">
                        <strong>Empresa:</strong> Arkheioncorp<br />
                        <strong>Endereço:</strong> São Paulo/SP, Brasil<br />
                        <strong>E-mail:</strong> privacidade@arkheioncorp.com<br />
                        <strong>DPO:</strong> dpo@arkheioncorp.com
                      </p>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 2 - Dados Coletados */}
                <AccordionItem value="section-2" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    2. Dados Pessoais que Coletamos
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 border rounded-lg">
                        <h4 className="font-medium text-foreground mb-2">📝 Dados de Cadastro</h4>
                        <ul className="text-sm space-y-1">
                          <li>• Nome completo</li>
                          <li>• Endereço de e-mail</li>
                          <li>• Telefone (opcional)</li>
                          <li>• Senha (criptografada)</li>
                          <li>• CPF/CNPJ (para pagamentos)</li>
                        </ul>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <h4 className="font-medium text-foreground mb-2">💻 Dados Técnicos</h4>
                        <ul className="text-sm space-y-1">
                          <li>• Endereço IP</li>
                          <li>• HWID do dispositivo</li>
                          <li>• Tipo de navegador/OS</li>
                          <li>• Logs de acesso</li>
                          <li>• Cookies e identificadores</li>
                        </ul>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <h4 className="font-medium text-foreground mb-2">📊 Dados de Uso</h4>
                        <ul className="text-sm space-y-1">
                          <li>• Produtos pesquisados</li>
                          <li>• Favoritos salvos</li>
                          <li>• Copies geradas</li>
                          <li>• Funcionalidades acessadas</li>
                          <li>• Tempo de uso</li>
                        </ul>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <h4 className="font-medium text-foreground mb-2">🔗 Dados de Integrações</h4>
                        <ul className="text-sm space-y-1">
                          <li>• Tokens de redes sociais</li>
                          <li>• Dados de contas conectadas</li>
                          <li>• Sessões do WhatsApp</li>
                          <li>• Métricas de publicações</li>
                        </ul>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 3 - Finalidades */}
                <AccordionItem value="section-3" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    3. Finalidades do Tratamento
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div className="space-y-3">
                      <div className="flex gap-3">
                        <span className="text-green-500">✅</span>
                        <div>
                          <strong>Execução de Contrato:</strong>
                          <p className="text-sm">Fornecer os serviços contratados, processar pagamentos, gerenciar sua conta</p>
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <span className="text-green-500">✅</span>
                        <div>
                          <strong>Legítimo Interesse:</strong>
                          <p className="text-sm">Melhorar serviços, prevenir fraudes, análise de uso, suporte ao cliente</p>
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <span className="text-green-500">✅</span>
                        <div>
                          <strong>Obrigação Legal:</strong>
                          <p className="text-sm">Cumprir obrigações fiscais, responder a autoridades, manter registros legais</p>
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <span className="text-green-500">✅</span>
                        <div>
                          <strong>Consentimento:</strong>
                          <p className="text-sm">Marketing direto, newsletters, cookies opcionais, integrações de terceiros</p>
                        </div>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 4 - Compartilhamento */}
                <AccordionItem value="section-4" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    4. Compartilhamento de Dados
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div className="p-4 bg-red-50 dark:bg-red-950/30 rounded-lg mb-4">
                      <p className="font-medium text-red-700 dark:text-red-400">
                        ❌ NÃO vendemos, alugamos ou comercializamos seus dados pessoais
                      </p>
                    </div>
                    
                    <p>Podemos compartilhar dados apenas com:</p>
                    <ul className="space-y-3 mt-4">
                      <li className="p-3 border rounded-lg">
                        <strong>MercadoPago</strong> - Processamento de pagamentos
                        <p className="text-sm">Dados de cobrança necessários para transações</p>
                      </li>
                      <li className="p-3 border rounded-lg">
                        <strong>OpenAI</strong> - Geração de conteúdo IA
                        <p className="text-sm">Prompts e contexto para gerar copies (anonimizados)</p>
                      </li>
                      <li className="p-3 border rounded-lg">
                        <strong>Plataformas Integradas</strong> - TikTok, Instagram, YouTube, WhatsApp
                        <p className="text-sm">Conforme suas autorizações específicas</p>
                      </li>
                      <li className="p-3 border rounded-lg">
                        <strong>Autoridades Legais</strong>
                        <p className="text-sm">Quando exigido por lei ou ordem judicial</p>
                      </li>
                    </ul>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 5 - Seus Direitos LGPD */}
                <AccordionItem value="section-5" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    5. Seus Direitos (LGPD - Art. 18)
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <p className="font-medium text-foreground">
                      Você tem os seguintes direitos garantidos pela LGPD:
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-3 border rounded-lg">
                        <strong>🔍 Confirmação</strong>
                        <p className="text-sm">Saber se tratamos seus dados</p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <strong>📥 Acesso</strong>
                        <p className="text-sm">Obter cópia dos seus dados</p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <strong>✏️ Correção</strong>
                        <p className="text-sm">Corrigir dados incorretos</p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <strong>🗑️ Eliminação</strong>
                        <p className="text-sm">Excluir dados desnecessários</p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <strong>📦 Portabilidade</strong>
                        <p className="text-sm">Receber dados em formato aberto</p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <strong>🚫 Revogação</strong>
                        <p className="text-sm">Retirar consentimento dado</p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <strong>ℹ️ Informação</strong>
                        <p className="text-sm">Saber com quem compartilhamos</p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <strong>⛔ Oposição</strong>
                        <p className="text-sm">Opor-se a tratamento indevido</p>
                      </div>
                    </div>
                    <div className="p-4 bg-tiktrend-primary/10 rounded-lg mt-4">
                      <p className="font-medium">Como exercer seus direitos:</p>
                      <p className="text-sm mt-2">
                        Envie e-mail para <a href="mailto:privacidade@arkheioncorp.com" className="text-tiktrend-primary hover:underline">privacidade@arkheioncorp.com</a> ou 
                        acesse <strong>Configurações → Privacidade</strong> no aplicativo.
                        Responderemos em até 15 dias.
                      </p>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 6 - Segurança */}
                <AccordionItem value="section-6" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    6. Segurança dos Dados
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <p>Implementamos medidas técnicas e organizacionais robustas:</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                      <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                        <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                          🔐 Criptografia
                        </h4>
                        <ul className="text-sm space-y-1">
                          <li>• TLS 1.3 em trânsito</li>
                          <li>• AES-256 em repouso</li>
                          <li>• Bcrypt para senhas</li>
                        </ul>
                      </div>
                      <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                        <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                          🛡️ Controles de Acesso
                        </h4>
                        <ul className="text-sm space-y-1">
                          <li>• Autenticação JWT</li>
                          <li>• RBAC (controle por roles)</li>
                          <li>• 2FA disponível</li>
                        </ul>
                      </div>
                      <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                        <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                          📊 Monitoramento
                        </h4>
                        <ul className="text-sm space-y-1">
                          <li>• Logs de auditoria</li>
                          <li>• Detecção de intrusão</li>
                          <li>• Alertas em tempo real</li>
                        </ul>
                      </div>
                      <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                        <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                          💾 Backup e Recuperação
                        </h4>
                        <ul className="text-sm space-y-1">
                          <li>• Backups diários</li>
                          <li>• Retenção 30 dias</li>
                          <li>• Testes de recovery</li>
                        </ul>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 7 - Retenção */}
                <AccordionItem value="section-7" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    7. Retenção de Dados
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div className="space-y-3">
                      <div className="p-3 border rounded-lg flex justify-between items-center">
                        <span>Dados de conta</span>
                        <span className="text-sm bg-muted px-2 py-1 rounded">Enquanto ativa + 30 dias</span>
                      </div>
                      <div className="p-3 border rounded-lg flex justify-between items-center">
                        <span>Dados de transação</span>
                        <span className="text-sm bg-muted px-2 py-1 rounded">5 anos (obrigação fiscal)</span>
                      </div>
                      <div className="p-3 border rounded-lg flex justify-between items-center">
                        <span>Logs de acesso</span>
                        <span className="text-sm bg-muted px-2 py-1 rounded">6 meses (Marco Civil)</span>
                      </div>
                      <div className="p-3 border rounded-lg flex justify-between items-center">
                        <span>Cookies de sessão</span>
                        <span className="text-sm bg-muted px-2 py-1 rounded">Até logout ou 24h</span>
                      </div>
                      <div className="p-3 border rounded-lg flex justify-between items-center">
                        <span>Dados de marketing</span>
                        <span className="text-sm bg-muted px-2 py-1 rounded">Até revogação</span>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 8 - Transferência Internacional */}
                <AccordionItem value="section-8" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    8. Transferência Internacional
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <p>
                      Alguns de nossos provedores de serviço podem estar localizados fora do Brasil. 
                      Garantimos proteção adequada através de:
                    </p>
                    <ul className="list-disc pl-6 mt-4 space-y-2">
                      <li>Cláusulas contratuais padrão aprovadas pela ANPD</li>
                      <li>Países com nível adequado de proteção</li>
                      <li>Certificações de privacidade (ex: Privacy Shield)</li>
                      <li>Consentimento específico quando necessário</li>
                    </ul>
                    <p className="text-sm mt-4">
                      Principais países: Brasil (principal), Estados Unidos (AWS, OpenAI)
                    </p>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 9 - Menores */}
                <AccordionItem value="section-9" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    9. Dados de Menores
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-950/30 rounded-lg">
                      <p className="font-medium text-yellow-700 dark:text-yellow-400">
                        ⚠️ Nossos serviços são destinados a maiores de 18 anos
                      </p>
                    </div>
                    <p>
                      Não coletamos intencionalmente dados de menores de idade. 
                      Se identificarmos que coletamos dados de um menor, excluiremos 
                      as informações imediatamente.
                    </p>
                    <p>
                      Se você acredita que um menor está usando nossos serviços, 
                      entre em contato: <a href="mailto:privacidade@arkheioncorp.com" className="text-tiktrend-primary">privacidade@arkheioncorp.com</a>
                    </p>
                  </AccordionContent>
                </AccordionItem>

              </Accordion>

              {/* Contato DPO */}
              <section className="mt-8 pt-8 border-t">
                <h2 className="text-2xl font-semibold mb-4">10. Contato do DPO</h2>
                <div className="p-6 bg-muted/50 rounded-lg">
                  <p className="mb-4">
                    Nosso Encarregado de Proteção de Dados (DPO) está disponível para 
                    atender suas solicitações:
                  </p>
                  <div className="space-y-2">
                    <p>
                      <strong>DPO:</strong>{" "}
                      <a href="mailto:dpo@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        dpo@arkheioncorp.com
                      </a>
                    </p>
                    <p>
                      <strong>Privacidade:</strong>{" "}
                      <a href="mailto:privacidade@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        privacidade@arkheioncorp.com
                      </a>
                    </p>
                    <p>
                      <strong>Prazo de resposta:</strong> Até 15 dias úteis
                    </p>
                  </div>
                </div>
              </section>

              {/* Links relacionados */}
              <section className="mt-8 pt-8 border-t">
                <h3 className="text-xl font-medium mb-4">Documentos Relacionados</h3>
                <div className="flex flex-wrap gap-4">
                  <Link to="/terms" className="text-tiktrend-primary hover:underline">
                    Termos de Uso →
                  </Link>
                  <Link to="/cookies" className="text-tiktrend-primary hover:underline">
                    Política de Cookies →
                  </Link>
                  <Link to="/acceptable-use" className="text-tiktrend-primary hover:underline">
                    Uso Aceitável →
                  </Link>
                </div>
              </section>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-muted-foreground">
          © 2025 Arkheioncorp. Todos os direitos reservados.
        </p>
      </main>

      <Footer minimal />
    </div>
  );
};

export default Privacy;
