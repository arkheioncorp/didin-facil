import * as React from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { TikTrendIcon } from "@/components/icons";
import { Footer } from "@/components/layout/Footer";

export const AcceptableUse: React.FC = () => {
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
              <h1 className="text-3xl font-bold mb-2">📋 Política de Uso Aceitável</h1>
              <p className="text-muted-foreground">
                Última atualização: {lastUpdated}
              </p>
            </div>

            <div className="prose prose-slate dark:prose-invert max-w-none space-y-8">
              {/* Seção 1 */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">1. Introdução</h2>
                <p className="text-muted-foreground leading-relaxed">
                  Esta Política de Uso Aceitável ("PUA") define as regras e diretrizes para uso 
                  do TikTrend Finder e serviços relacionados. O descumprimento pode resultar em 
                  suspensão ou cancelamento da sua conta.
                </p>
              </section>

              {/* Seção 2 - Uso Permitido */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">2. Uso Permitido</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                    <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                      ✅ Pesquisa de Produtos
                    </h4>
                    <ul className="text-sm space-y-1 text-green-600 dark:text-green-400">
                      <li>• Pesquisar produtos para dropshipping</li>
                      <li>• Analisar tendências de mercado</li>
                      <li>• Comparar preços e características</li>
                    </ul>
                  </div>
                  
                  <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                    <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                      ✅ Marketing Legítimo
                    </h4>
                    <ul className="text-sm space-y-1 text-green-600 dark:text-green-400">
                      <li>• Criar conteúdo para suas redes sociais</li>
                      <li>• Gerar copies para seus anúncios</li>
                      <li>• Desenvolver estratégias de marketing</li>
                    </ul>
                  </div>
                  
                  <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                    <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                      ✅ Automação Responsável
                    </h4>
                    <ul className="text-sm space-y-1 text-green-600 dark:text-green-400">
                      <li>• Automatizar publicações em suas contas</li>
                      <li>• Gerenciar múltiplas contas de sua propriedade</li>
                      <li>• Agendar posts dentro dos limites</li>
                    </ul>
                  </div>
                  
                  <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                    <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                      ✅ Integração com Terceiros
                    </h4>
                    <ul className="text-sm space-y-1 text-green-600 dark:text-green-400">
                      <li>• Conectar suas contas de redes sociais</li>
                      <li>• Usar APIs conforme documentação</li>
                      <li>• Integrar com ferramentas complementares</li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* Seção 3 - Uso Proibido */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">3. Uso Proibido</h2>
                
                <div className="space-y-6">
                  <div className="p-4 border border-red-200 dark:border-red-900 rounded-lg bg-red-50 dark:bg-red-950/30">
                    <h4 className="font-medium text-red-700 dark:text-red-400 mb-3">
                      ❌ Atividades Ilegais
                    </h4>
                    <ul className="text-sm space-y-1 text-red-600 dark:text-red-400 grid grid-cols-1 md:grid-cols-2 gap-1">
                      <li>• Violação de leis federais, estaduais ou locais</li>
                      <li>• Lavagem de dinheiro</li>
                      <li>• Evasão fiscal ou fraude financeira</li>
                      <li>• Violação de direitos autorais</li>
                      <li>• Tráfico de produtos proibidos</li>
                      <li>• Qualquer atividade criminosa</li>
                    </ul>
                  </div>

                  <div className="p-4 border border-red-200 dark:border-red-900 rounded-lg bg-red-50 dark:bg-red-950/30">
                    <h4 className="font-medium text-red-700 dark:text-red-400 mb-3">
                      ❌ Fraude e Engano
                    </h4>
                    <ul className="text-sm space-y-1 text-red-600 dark:text-red-400 grid grid-cols-1 md:grid-cols-2 gap-1">
                      <li>• Criar avaliações falsas ou enganosas</li>
                      <li>• Impersonar outras pessoas ou empresas</li>
                      <li>• Usar informações falsas no cadastro</li>
                      <li>• Manipular métricas ou estatísticas</li>
                      <li>• Enganar consumidores sobre produtos</li>
                      <li>• Golpes ou esquemas fraudulentos</li>
                    </ul>
                  </div>

                  <div className="p-4 border border-red-200 dark:border-red-900 rounded-lg bg-red-50 dark:bg-red-950/30">
                    <h4 className="font-medium text-red-700 dark:text-red-400 mb-3">
                      ❌ Spam e Abuso
                    </h4>
                    <ul className="text-sm space-y-1 text-red-600 dark:text-red-400 grid grid-cols-1 md:grid-cols-2 gap-1">
                      <li>• Mensagens não solicitadas em massa</li>
                      <li>• Múltiplas contas para contornar limites</li>
                      <li>• Automação que viole ToS de plataformas</li>
                      <li>• Sobrecarregar sistemas com requisições</li>
                      <li>• Scraping não autorizado de dados</li>
                      <li>• Degradar experiência de outros usuários</li>
                    </ul>
                  </div>

                  <div className="p-4 border border-red-200 dark:border-red-900 rounded-lg bg-red-50 dark:bg-red-950/30">
                    <h4 className="font-medium text-red-700 dark:text-red-400 mb-3">
                      ❌ Conteúdo Proibido
                    </h4>
                    <ul className="text-sm space-y-1 text-red-600 dark:text-red-400 grid grid-cols-1 md:grid-cols-2 gap-1">
                      <li>• Pornografia ou conteúdo sexualmente explícito</li>
                      <li>• Material de abuso infantil (CSAM)</li>
                      <li>• Discurso de ódio ou discriminação</li>
                      <li>• Conteúdo que promova violência</li>
                      <li>• Desinformação ou fake news maliciosas</li>
                      <li>• Conteúdo difamatório ou calunioso</li>
                    </ul>
                  </div>

                  <div className="p-4 border border-red-200 dark:border-red-900 rounded-lg bg-red-50 dark:bg-red-950/30">
                    <h4 className="font-medium text-red-700 dark:text-red-400 mb-3">
                      ❌ Segurança e Integridade
                    </h4>
                    <ul className="text-sm space-y-1 text-red-600 dark:text-red-400 grid grid-cols-1 md:grid-cols-2 gap-1">
                      <li>• Acessar sistemas não autorizados</li>
                      <li>• Engenharia reversa do software</li>
                      <li>• Introduzir malware ou código malicioso</li>
                      <li>• Contornar medidas de segurança</li>
                      <li>• Compartilhar credenciais ou tokens</li>
                      <li>• Ataques de negação de serviço</li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* Seção 4 - Limites */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">4. Limites de Uso</h2>
                
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Recurso</TableHead>
                      <TableHead>Limite</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell>Requisições API</TableCell>
                      <TableCell>1.000/hora</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Uploads por dia</TableCell>
                      <TableCell>50</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Contas conectadas</TableCell>
                      <TableCell>10 por plataforma</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Armazenamento</TableCell>
                      <TableCell>5GB</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Mensagens automáticas</TableCell>
                      <TableCell>500/dia</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>

                <p className="text-sm text-muted-foreground mt-4">
                  <strong>Fair Use:</strong> Uso que exceda significativamente a média pode ser 
                  limitado. Padrões de uso são monitorados e notificaremos antes de aplicar restrições.
                </p>
              </section>

              {/* Seção 5 - Integrações */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">5. Integrações de Terceiros</h2>
                
                <p className="text-muted-foreground mb-4">
                  Ao usar integrações com TikTok, Instagram, YouTube, WhatsApp, etc.:
                </p>
                
                <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-6">
                  <li>Você é responsável por cumprir os ToS de cada plataforma</li>
                  <li>Violações podem resultar em banimento nessas plataformas</li>
                  <li>Não nos responsabilizamos por suspensões em serviços de terceiros</li>
                </ul>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 border rounded-lg">
                    <strong>TikTok</strong>
                    <p className="text-sm text-muted-foreground">
                      Siga as Diretrizes da Comunidade. Não use automação para inflar métricas.
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <strong>Instagram/Meta</strong>
                    <p className="text-sm text-muted-foreground">
                      Cumpra Termos de Uso. Não faça follow/unfollow massivo.
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <strong>YouTube</strong>
                    <p className="text-sm text-muted-foreground">
                      Respeite políticas de monetização e diretrizes de copyright.
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <strong>WhatsApp</strong>
                    <p className="text-sm text-muted-foreground">
                      Apenas para comunicação legítima. Obtenha consentimento antes de enviar.
                    </p>
                  </div>
                </div>
              </section>

              {/* Seção 6 - Consequências */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">6. Monitoramento e Aplicação</h2>
                
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Violação</TableHead>
                      <TableHead>Consequência</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="text-yellow-600 dark:text-yellow-400">Menor</TableCell>
                      <TableCell>Aviso por e-mail</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="text-orange-600 dark:text-orange-400">Moderada</TableCell>
                      <TableCell>Suspensão temporária (7-30 dias)</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="text-red-600 dark:text-red-400">Grave</TableCell>
                      <TableCell>Suspensão por tempo indeterminado</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="text-red-700 dark:text-red-500 font-medium">Crítica</TableCell>
                      <TableCell>Cancelamento permanente</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="text-red-900 dark:text-red-300 font-bold">Ilegal</TableCell>
                      <TableCell>Cancelamento + reporte às autoridades</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>

                <div className="mt-6 p-4 bg-muted/50 rounded-lg">
                  <h4 className="font-medium mb-2">Processo de Apelação</h4>
                  <ol className="list-decimal pl-6 space-y-1 text-sm text-muted-foreground">
                    <li>Você receberá notificação com motivo da suspensão</li>
                    <li>Pode apelar em até 14 dias</li>
                    <li>Envie apelação para: <a href="mailto:appeals@arkheioncorp.com" className="text-tiktrend-primary">appeals@arkheioncorp.com</a></li>
                    <li>Revisaremos e responderemos em 7 dias úteis</li>
                    <li>Nossa decisão final é definitiva</li>
                  </ol>
                </div>
              </section>

              {/* Seção 7 - Denúncias */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">7. Denúncias</h2>
                
                <p className="text-muted-foreground mb-4">
                  Se você identificar violação desta política:
                </p>
                
                <div className="p-6 bg-muted/50 rounded-lg">
                  <div className="space-y-2 mb-4">
                    <p>
                      <strong>E-mail:</strong>{" "}
                      <a href="mailto:abuse@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        abuse@arkheioncorp.com
                      </a>
                    </p>
                    <p>
                      <strong>Formulário:</strong>{" "}
                      <a href="https://arkheioncorp.com/report" target="_blank" rel="noopener noreferrer" className="text-tiktrend-primary hover:underline">
                        arkheioncorp.com/report
                      </a>
                    </p>
                  </div>
                  
                  <h4 className="font-medium mb-2">O que incluir na denúncia:</h4>
                  <ul className="list-disc pl-6 space-y-1 text-sm text-muted-foreground">
                    <li>Descrição da violação</li>
                    <li>Evidências (screenshots, links)</li>
                    <li>Identificação do usuário (se conhecido)</li>
                    <li>Data e hora aproximadas</li>
                  </ul>
                  
                  <p className="text-sm text-muted-foreground mt-4">
                    <strong>Confidencialidade:</strong> Relatórios são tratados com confidencialidade. 
                    Não revelaremos sua identidade ao denunciado, exceto se exigido por lei.
                  </p>
                </div>
              </section>

              {/* Seção 8 - Contato */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">8. Contato</h2>
                <div className="p-6 bg-muted/50 rounded-lg">
                  <div className="space-y-2">
                    <p>
                      <strong>Abuse:</strong>{" "}
                      <a href="mailto:abuse@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        abuse@arkheioncorp.com
                      </a>
                    </p>
                    <p>
                      <strong>Apelações:</strong>{" "}
                      <a href="mailto:appeals@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        appeals@arkheioncorp.com
                      </a>
                    </p>
                    <p>
                      <strong>Geral:</strong>{" "}
                      <a href="mailto:suporte@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        suporte@arkheioncorp.com
                      </a>
                    </p>
                  </div>
                </div>
              </section>

              {/* Links relacionados */}
              <section className="pt-8 border-t">
                <h3 className="text-xl font-medium mb-4">Documentos Relacionados</h3>
                <div className="flex flex-wrap gap-4">
                  <Link to="/terms" className="text-tiktrend-primary hover:underline">
                    Termos de Uso →
                  </Link>
                  <Link to="/privacy" className="text-tiktrend-primary hover:underline">
                    Política de Privacidade →
                  </Link>
                  <Link to="/cookies" className="text-tiktrend-primary hover:underline">
                    Política de Cookies →
                  </Link>
                </div>
              </section>
            </div>
          </CardContent>
        </Card>
      </main>

      <Footer minimal />
    </div>
  );
};

export default AcceptableUse;
