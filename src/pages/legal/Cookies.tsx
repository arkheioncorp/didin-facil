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

export const Cookies: React.FC = () => {
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
              <h1 className="text-3xl font-bold mb-2">🍪 Política de Cookies</h1>
              <p className="text-muted-foreground">
                Última atualização: {lastUpdated}
              </p>
            </div>

            <div className="prose prose-slate dark:prose-invert max-w-none space-y-8">
              {/* Seção 1 */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">1. O Que São Cookies?</h2>
                <p className="text-muted-foreground leading-relaxed">
                  Cookies são pequenos arquivos de texto armazenados em seu dispositivo (computador, 
                  tablet ou celular) quando você visita um website ou usa um aplicativo. Eles permitem 
                  que o site reconheça seu dispositivo e lembre informações sobre sua visita.
                </p>
                
                <h3 className="text-xl font-medium mt-6 mb-3">Tecnologias Similares</h3>
                <p className="text-muted-foreground leading-relaxed mb-4">
                  Além de cookies, também utilizamos:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                  <li><strong>Local Storage:</strong> Armazenamento local no navegador/aplicativo</li>
                  <li><strong>Session Storage:</strong> Dados temporários de sessão</li>
                  <li><strong>Pixels de rastreamento:</strong> Imagens invisíveis para analytics</li>
                  <li><strong>Web Beacons:</strong> Tecnologias similares a pixels</li>
                  <li><strong>Fingerprinting de dispositivo:</strong> Identificação baseada em características</li>
                </ul>
              </section>

              {/* Seção 2 */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">2. Como Usamos Cookies</h2>
                
                <h3 className="text-xl font-medium mt-6 mb-3">🔒 Cookies Estritamente Necessários</h3>
                <p className="text-sm text-yellow-600 dark:text-yellow-400 mb-4">
                  Não podem ser desativados - essenciais para o funcionamento
                </p>
                <Table className="mb-6">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cookie</TableHead>
                      <TableHead>Finalidade</TableHead>
                      <TableHead>Duração</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-mono">session_id</TableCell>
                      <TableCell>Autenticação de usuário</TableCell>
                      <TableCell>Sessão</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">csrf_token</TableCell>
                      <TableCell>Proteção contra CSRF</TableCell>
                      <TableCell>Sessão</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">auth_token</TableCell>
                      <TableCell>Token JWT de acesso</TableCell>
                      <TableCell>12 horas</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">refresh_token</TableCell>
                      <TableCell>Renovação de sessão</TableCell>
                      <TableCell>30 dias</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">device_id</TableCell>
                      <TableCell>Identificação do dispositivo</TableCell>
                      <TableCell>1 ano</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>

                <h3 className="text-xl font-medium mt-6 mb-3">⚙️ Cookies de Funcionalidade</h3>
                <p className="text-sm text-green-600 dark:text-green-400 mb-4">
                  Podem ser desativados nas configurações
                </p>
                <Table className="mb-6">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cookie</TableHead>
                      <TableHead>Finalidade</TableHead>
                      <TableHead>Duração</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-mono">theme</TableCell>
                      <TableCell>Preferência de tema (claro/escuro)</TableCell>
                      <TableCell>1 ano</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">language</TableCell>
                      <TableCell>Idioma preferido</TableCell>
                      <TableCell>1 ano</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">sidebar_collapsed</TableCell>
                      <TableCell>Estado da barra lateral</TableCell>
                      <TableCell>1 ano</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">last_search</TableCell>
                      <TableCell>Última busca realizada</TableCell>
                      <TableCell>30 dias</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">filters</TableCell>
                      <TableCell>Filtros salvos</TableCell>
                      <TableCell>90 dias</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>

                <h3 className="text-xl font-medium mt-6 mb-3">📊 Cookies de Analytics</h3>
                <p className="text-sm text-green-600 dark:text-green-400 mb-4">
                  Podem ser desativados nas configurações
                </p>
                <Table className="mb-6">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cookie</TableHead>
                      <TableHead>Provedor</TableHead>
                      <TableHead>Finalidade</TableHead>
                      <TableHead>Duração</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-mono">_pk_id</TableCell>
                      <TableCell>PostHog</TableCell>
                      <TableCell>Identificador de usuário</TableCell>
                      <TableCell>2 anos</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">_pk_ses</TableCell>
                      <TableCell>PostHog</TableCell>
                      <TableCell>Sessão de analytics</TableCell>
                      <TableCell>30 min</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-mono">ph_*</TableCell>
                      <TableCell>PostHog</TableCell>
                      <TableCell>Eventos de produto</TableCell>
                      <TableCell>Variável</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </section>

              {/* Seção 3 */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">3. Cookies de Terceiros</h2>
                
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium">MercadoPago</h4>
                    <p className="text-sm text-muted-foreground">Processamento seguro de pagamentos</p>
                    <a 
                      href="https://www.mercadopago.com.br/privacidade" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-tiktrend-primary hover:underline"
                    >
                      Ver política →
                    </a>
                  </div>
                  
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium">PostHog</h4>
                    <p className="text-sm text-muted-foreground">Analytics de produto</p>
                    <a 
                      href="https://posthog.com/privacy" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-tiktrend-primary hover:underline"
                    >
                      Ver política →
                    </a>
                  </div>
                  
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium">Sentry</h4>
                    <p className="text-sm text-muted-foreground">Monitoramento de erros</p>
                    <a 
                      href="https://sentry.io/privacy/" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-tiktrend-primary hover:underline"
                    >
                      Ver política →
                    </a>
                  </div>
                  
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium">Cloudflare</h4>
                    <p className="text-sm text-muted-foreground">CDN, DDoS protection, WAF</p>
                    <a 
                      href="https://www.cloudflare.com/privacypolicy/" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-tiktrend-primary hover:underline"
                    >
                      Ver política →
                    </a>
                  </div>
                </div>
              </section>

              {/* Seção 4 */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">4. Gerenciando Cookies</h2>
                
                <h3 className="text-xl font-medium mt-6 mb-3">No Aplicativo</h3>
                <p className="text-muted-foreground mb-4">
                  Acesse <strong>Configurações → Privacidade → Cookies</strong> para:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                  <li>Ver cookies ativos</li>
                  <li>Desativar cookies opcionais</li>
                  <li>Limpar dados armazenados</li>
                  <li>Exportar configurações</li>
                </ul>

                <h3 className="text-xl font-medium mt-6 mb-3">No Navegador</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 border rounded-lg">
                    <strong>Chrome:</strong>
                    <p className="text-sm text-muted-foreground">
                      Configurações → Privacidade e segurança → Cookies
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <strong>Firefox:</strong>
                    <p className="text-sm text-muted-foreground">
                      Configurações → Privacidade e Segurança → Cookies
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <strong>Safari:</strong>
                    <p className="text-sm text-muted-foreground">
                      Preferências → Privacidade → Gerenciar Dados de Sites
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <strong>Edge:</strong>
                    <p className="text-sm text-muted-foreground">
                      Configurações → Privacidade → Cookies
                    </p>
                  </div>
                </div>
              </section>

              {/* Seção 5 */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">5. Impacto da Desativação</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 border border-red-200 dark:border-red-900 rounded-lg bg-red-50 dark:bg-red-950/30">
                    <h4 className="font-medium text-red-700 dark:text-red-400 mb-2">
                      Cookies Necessários
                    </h4>
                    <ul className="text-sm space-y-1 text-red-600 dark:text-red-400">
                      <li>❌ Não conseguirá fazer login</li>
                      <li>❌ Sessões expirarão imediatamente</li>
                      <li>❌ Funcionalidades básicas falharão</li>
                    </ul>
                  </div>
                  
                  <div className="p-4 border border-yellow-200 dark:border-yellow-900 rounded-lg bg-yellow-50 dark:bg-yellow-950/30">
                    <h4 className="font-medium text-yellow-700 dark:text-yellow-400 mb-2">
                      Cookies de Funcionalidade
                    </h4>
                    <ul className="text-sm space-y-1 text-yellow-600 dark:text-yellow-400">
                      <li>⚠️ Preferências não serão salvas</li>
                      <li>⚠️ Configurar a cada acesso</li>
                      <li>⚠️ Experiência menos personalizada</li>
                    </ul>
                  </div>
                  
                  <div className="p-4 border border-green-200 dark:border-green-900 rounded-lg bg-green-50 dark:bg-green-950/30">
                    <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">
                      Cookies de Analytics
                    </h4>
                    <ul className="text-sm space-y-1 text-green-600 dark:text-green-400">
                      <li>✅ Privacidade aumentada</li>
                      <li>⚠️ Menos melhorias baseadas em uso</li>
                      <li>✅ Funcionalidades principais OK</li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* Seção 6 */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">6. Cookies e Menores</h2>
                <p className="text-muted-foreground">
                  Não coletamos intencionalmente dados de menores de 18 anos. Se você acredita 
                  que um menor está usando nossos serviços, entre em contato conosco.
                </p>
              </section>

              {/* Seção 7 */}
              <section>
                <h2 className="text-2xl font-semibold mb-4">7. Contato</h2>
                <div className="p-6 bg-muted/50 rounded-lg">
                  <p className="mb-4">Para dúvidas sobre cookies:</p>
                  <div className="space-y-2">
                    <p>
                      <strong>E-mail:</strong>{" "}
                      <a href="mailto:privacidade@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        privacidade@arkheioncorp.com
                      </a>
                    </p>
                    <p>
                      <strong>DPO:</strong>{" "}
                      <a href="mailto:dpo@arkheioncorp.com" className="text-tiktrend-primary hover:underline">
                        dpo@arkheioncorp.com
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
                  <Link to="/acceptable-use" className="text-tiktrend-primary hover:underline">
                    Uso Aceitável →
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

export default Cookies;
