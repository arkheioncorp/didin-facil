/**
 * Terms of Service Page
 * Página pública para Termos de Serviço - Versão Completa
 */

import * as React from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TikTrendIcon } from "@/components/icons";
import { Footer } from "@/components/layout/Footer";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export const Terms: React.FC = () => {
  const lastUpdated = "30 de novembro de 2025";
  const version = "1.0.0";

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
              <h1 className="text-3xl font-bold mb-2">📜 Termos de Serviço</h1>
              <p className="text-muted-foreground">
                Última atualização: {lastUpdated} | Versão: {version}
              </p>
            </div>

            {/* Aviso importante */}
            <div className="p-4 mb-8 bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-900 rounded-lg">
              <p className="text-sm text-yellow-700 dark:text-yellow-400">
                <strong>⚠️ Importante:</strong> Ao usar o TikTrend Finder, você concorda com estes termos. 
                Leia atentamente antes de continuar.
              </p>
            </div>

            <div className="prose prose-slate dark:prose-invert max-w-none">
              <Accordion type="multiple" className="w-full space-y-4">
                
                {/* Seção 1 */}
                <AccordionItem value="section-1" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    1. Aceitação dos Termos
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">1.1 Acordo Vinculativo</h4>
                      <p>
                        Ao acessar, baixar, instalar ou utilizar o software TikTrend Finder ("Software"), 
                        aplicativo móvel, website ou qualquer serviço relacionado (coletivamente, "Serviços") 
                        fornecidos pela Arkheioncorp ("Empresa", "nós", "nosso"), você ("Usuário", "você", "seu") 
                        concorda em ficar vinculado a estes Termos de Serviço ("Termos").
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">1.2 Capacidade Legal</h4>
                      <p>Você declara e garante que:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Tem pelo menos 18 (dezoito) anos de idade ou a maioridade legal em sua jurisdição</li>
                        <li>Possui plena capacidade civil para celebrar este contrato</li>
                        <li>Não está impedido de usar os Serviços por qualquer lei aplicável</li>
                        <li>Se representa uma empresa, tem autoridade para vincular essa entidade a estes Termos</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">1.3 Alterações nos Termos</h4>
                      <p>
                        Reservamo-nos o direito de modificar estes Termos a qualquer momento. Notificaremos 
                        sobre alterações materiais com pelo menos 30 (trinta) dias de antecedência. O uso 
                        continuado dos Serviços após as alterações constitui aceitação dos novos Termos.
                      </p>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 2 */}
                <AccordionItem value="section-2" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    2. Descrição dos Serviços
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">2.1 O que Oferecemos</h4>
                      <p>O TikTrend Finder é uma plataforma de software que oferece:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Agregação de dados públicos de produtos de e-commerce</li>
                        <li>Ferramentas de análise e filtragem de produtos</li>
                        <li>Geração de conteúdo assistida por inteligência artificial</li>
                        <li>Gerenciamento de listas de produtos favoritos</li>
                        <li>Integração com redes sociais para publicação de conteúdo</li>
                        <li>Ferramentas de CRM e automação de marketing</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">2.2 Natureza dos Dados</h4>
                      <p>Os dados apresentados nos Serviços são:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Coletados de fontes públicas disponíveis na internet</li>
                        <li>Fornecidos "como estão", sem garantia de precisão ou atualidade</li>
                        <li>Sujeitos a alterações sem aviso prévio</li>
                        <li>Não constituem recomendação de investimento ou negócio</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">2.3 Disponibilidade</h4>
                      <ul className="list-disc pl-6 space-y-1">
                        <li>Os Serviços são fornecidos "conforme disponibilidade"</li>
                        <li>Podemos suspender temporariamente para manutenção</li>
                        <li>Não garantimos disponibilidade ininterrupta</li>
                        <li>Reservamo-nos o direito de descontinuar recursos específicos</li>
                      </ul>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 3 */}
                <AccordionItem value="section-3" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    3. Conta de Usuário
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">3.1 Registro</h4>
                      <p>Para acessar funcionalidades completas, você deve:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Criar uma conta com informações precisas e atualizadas</li>
                        <li>Fornecer endereço de e-mail válido</li>
                        <li>Criar senha forte e segura</li>
                        <li>Manter suas credenciais confidenciais</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">3.2 Responsabilidade pela Conta</h4>
                      <p>Você é exclusivamente responsável por:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Todas as atividades realizadas em sua conta</li>
                        <li>Manter a confidencialidade de suas credenciais</li>
                        <li>Notificar-nos imediatamente sobre uso não autorizado</li>
                        <li>Danos resultantes de acesso não autorizado devido a negligência sua</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">3.3 Uma Conta por Pessoa</h4>
                      <ul className="list-disc pl-6 space-y-1">
                        <li>Cada pessoa física pode ter apenas uma conta</li>
                        <li>Contas não são transferíveis</li>
                        <li>Compartilhamento de contas é expressamente proibido</li>
                        <li>Violações resultarão em suspensão ou cancelamento</li>
                      </ul>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 4 */}
                <AccordionItem value="section-4" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    4. Licenciamento e Propriedade Intelectual
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">4.1 Licença de Uso</h4>
                      <p>Concedemos a você uma licença:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li><strong>Limitada:</strong> Apenas para uso dos Serviços conforme descrito</li>
                        <li><strong>Não-exclusiva:</strong> Outros usuários têm direitos similares</li>
                        <li><strong>Revogável:</strong> Podemos revogar por violação dos Termos</li>
                        <li><strong>Intransferível:</strong> Não pode ser cedida a terceiros</li>
                        <li><strong>Pessoal:</strong> Apenas para seu uso individual ou empresarial autorizado</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">4.2 Restrições</h4>
                      <p className="text-red-600 dark:text-red-400">Você concorda em NÃO:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Copiar, modificar, adaptar ou criar obras derivadas do Software</li>
                        <li>Fazer engenharia reversa, descompilar ou desmontar o Software</li>
                        <li>Remover avisos de direitos autorais ou marcas registradas</li>
                        <li>Sublicenciar, alugar, emprestar ou vender os Serviços</li>
                        <li>Usar o Software para criar produto concorrente</li>
                        <li>Extrair sistematicamente dados para uso comercial não autorizado</li>
                      </ul>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 5 */}
                <AccordionItem value="section-5" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    5. Pagamentos e Assinaturas
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">5.1 Modelos de Preço</h4>
                      <p>Oferecemos diferentes modelos de pagamento:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li><strong>Licença Vitalícia:</strong> Pagamento único com acesso permanente</li>
                        <li><strong>Créditos IA:</strong> Pacotes de créditos para funcionalidades de IA</li>
                        <li><strong>Combos:</strong> Pacotes com descontos especiais</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">5.2 Processamento de Pagamentos</h4>
                      <ul className="list-disc pl-6 space-y-1">
                        <li>Pagamentos são processados via MercadoPago</li>
                        <li>Aceitamos Pix, cartão de crédito e boleto bancário</li>
                        <li>Preços podem ser alterados com 30 dias de aviso prévio</li>
                        <li>Alterações não afetam licenças já adquiridas</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">5.3 Política de Reembolso</h4>
                      <ul className="list-disc pl-6 space-y-1">
                        <li><strong>Licença Vitalícia:</strong> Reembolso em até 7 (sete) dias após compra</li>
                        <li><strong>Créditos IA:</strong> Reembolso proporcional a créditos não utilizados</li>
                        <li>Reembolsos são processados pelo mesmo método de pagamento</li>
                        <li>Fraude ou abuso cancela direito a reembolso</li>
                      </ul>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 6 */}
                <AccordionItem value="section-6" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    6. Uso Aceitável
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">6.1 Condutas Permitidas</h4>
                      <p className="text-green-600 dark:text-green-400">Você pode usar os Serviços para:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Pesquisar produtos para atividades comerciais legítimas</li>
                        <li>Gerar conteúdo para suas próprias campanhas de marketing</li>
                        <li>Gerenciar listas de produtos de seu interesse</li>
                        <li>Automatizar publicações em suas próprias contas de redes sociais</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">6.2 Condutas Proibidas</h4>
                      <p className="text-red-600 dark:text-red-400 mb-2">É EXPRESSAMENTE PROIBIDO:</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <strong>Legais:</strong>
                          <ul className="list-disc pl-6 mt-1 space-y-1 text-sm">
                            <li>Violar qualquer lei ou direito de terceiros</li>
                            <li>Atividades fraudulentas ou ilegais</li>
                            <li>Violar LGPD/GDPR</li>
                          </ul>
                        </div>
                        <div>
                          <strong>Técnicas:</strong>
                          <ul className="list-disc pl-6 mt-1 space-y-1 text-sm">
                            <li>Acessar sistemas não autorizados</li>
                            <li>Introduzir malware</li>
                            <li>Contornar medidas de segurança</li>
                          </ul>
                        </div>
                        <div>
                          <strong>Comerciais:</strong>
                          <ul className="list-disc pl-6 mt-1 space-y-1 text-sm">
                            <li>Revender os Serviços</li>
                            <li>Criar produto concorrente</li>
                            <li>Extrair dados para banco próprio</li>
                          </ul>
                        </div>
                        <div>
                          <strong>Conteúdo:</strong>
                          <ul className="list-disc pl-6 mt-1 space-y-1 text-sm">
                            <li>Spam ou comunicações não solicitadas</li>
                            <li>Impersonar pessoas/empresas</li>
                            <li>Promover ódio ou violência</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 7 */}
                <AccordionItem value="section-7" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    7. Integrações com Terceiros
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">7.1 Plataformas de Terceiros</h4>
                      <p>Os Serviços podem integrar-se com:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>TikTok Shop e TikTok</li>
                        <li>Instagram e Facebook (Meta)</li>
                        <li>YouTube e Google</li>
                        <li>WhatsApp (via Evolution API)</li>
                        <li>Outros marketplaces e redes sociais</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">7.2 Termos de Terceiros</h4>
                      <p>Ao usar integrações, você concorda com:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Termos de serviço das respectivas plataformas</li>
                        <li>Políticas de privacidade de terceiros</li>
                        <li>Limitações de uso impostas por cada plataforma</li>
                        <li>Riscos de alterações unilaterais por terceiros</li>
                      </ul>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 8 */}
                <AccordionItem value="section-8" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    8. Inteligência Artificial
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">8.1 Funcionalidades de IA</h4>
                      <p>Oferecemos funcionalidades de IA para:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Geração de textos de marketing (copies)</li>
                        <li>Sugestões de hashtags e legendas</li>
                        <li>Análise de tendências e produtos</li>
                        <li>Chatbots e automação de atendimento</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">8.2 Limitações da IA</h4>
                      <p>Você reconhece que:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Conteúdo gerado por IA pode conter erros ou imprecisões</li>
                        <li>IA não substitui julgamento humano profissional</li>
                        <li>Você é responsável por revisar e aprovar conteúdo gerado</li>
                        <li>Uso de IA pode estar sujeito a termos de provedores (OpenAI)</li>
                      </ul>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 9 */}
                <AccordionItem value="section-9" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    9. Privacidade e Dados (LGPD)
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">9.1 Seus Direitos (LGPD)</h4>
                      <p>Você tem direito a:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Confirmar existência de tratamento</li>
                        <li>Acessar seus dados</li>
                        <li>Corrigir dados incompletos ou inexatos</li>
                        <li>Solicitar anonimização ou eliminação</li>
                        <li>Revogar consentimento</li>
                        <li>Solicitar portabilidade</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">9.2 Segurança de Dados</h4>
                      <p>Implementamos medidas de segurança incluindo:</p>
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        <li>Criptografia em trânsito (TLS 1.3) e em repouso</li>
                        <li>Controles de acesso e autenticação</li>
                        <li>Monitoramento e detecção de intrusões</li>
                        <li>Backups regulares e recuperação de desastres</li>
                      </ul>
                    </div>
                    <p className="mt-4">
                      Para mais detalhes, consulte nossa{" "}
                      <Link to="/privacy" className="text-tiktrend-primary hover:underline">
                        Política de Privacidade
                      </Link>
                      .
                    </p>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 10 */}
                <AccordionItem value="section-10" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    10. Isenção de Garantias
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-950/30 rounded-lg">
                      <p className="font-medium text-yellow-700 dark:text-yellow-400 mb-2">
                        "COMO ESTÁ"
                      </p>
                      <p className="text-sm">
                        OS SERVIÇOS SÃO FORNECIDOS "COMO ESTÃO" E "CONFORME DISPONÍVEIS", 
                        SEM GARANTIAS DE QUALQUER TIPO, EXPRESSAS OU IMPLÍCITAS.
                      </p>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 11 */}
                <AccordionItem value="section-11" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    11. Limitação de Responsabilidade
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <div className="p-4 bg-red-50 dark:bg-red-950/30 rounded-lg">
                      <p className="font-medium text-red-700 dark:text-red-400 mb-2">
                        Limite Máximo
                      </p>
                      <p className="text-sm">
                        Nossa responsabilidade total será limitada ao maior valor entre 
                        R$ 100,00 ou o valor pago por você nos últimos 12 meses.
                      </p>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Seção 12 */}
                <AccordionItem value="section-12" className="border rounded-lg px-4">
                  <AccordionTrigger className="text-lg font-semibold">
                    12. Lei Aplicável e Foro
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 text-muted-foreground">
                    <p>
                      Estes Termos são regidos pelas leis da República Federativa do Brasil, 
                      especialmente o Código Civil, Código de Defesa do Consumidor, LGPD e Marco Civil da Internet.
                    </p>
                    <p>
                      Fica eleito o foro da Comarca de São Paulo/SP para dirimir controvérsias.
                    </p>
                  </AccordionContent>
                </AccordionItem>

              </Accordion>

              {/* Contato */}
              <section className="mt-8 pt-8 border-t">
                <h2 className="text-2xl font-semibold mb-4">13. Contato</h2>
                <div className="p-6 bg-muted/50 rounded-lg">
                  <p className="mb-4">Para questões sobre estes Termos:</p>
                  <div className="space-y-2">
                    <p>
                      <strong>E-mail Legal:</strong>{" "}
                      <a href="mailto:legal@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        legal@arkheioncorp.com
                      </a>
                    </p>
                    <p>
                      <strong>Suporte:</strong>{" "}
                      <a href="mailto:suporte@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        suporte@arkheioncorp.com
                      </a>
                    </p>
                  </div>
                </div>
              </section>

              {/* Aceite */}
              <section className="mt-8 p-6 bg-tiktrend-primary/10 rounded-lg text-center">
                <p className="font-medium">
                  Ao usar nossos Serviços, você confirma que leu, entendeu e concorda com 
                  estes Termos de Serviço.
                </p>
              </section>

              {/* Links relacionados */}
              <section className="mt-8 pt-8 border-t">
                <h3 className="text-xl font-medium mb-4">Documentos Relacionados</h3>
                <div className="flex flex-wrap gap-4">
                  <Link to="/privacy" className="text-tiktrend-primary hover:underline">
                    Política de Privacidade →
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

export default Terms;
