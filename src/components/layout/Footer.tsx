import * as React from "react";
import { Link } from "react-router-dom";
import { TikTrendIcon } from "@/components/icons";
import { cn } from "@/lib/utils";
import { ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FooterProps {
  className?: string;
  minimal?: boolean;
}

export const Footer: React.FC<FooterProps> = ({ className, minimal = false }) => {
  const currentYear = new Date().getFullYear();
  const [isExpanded, setIsExpanded] = React.useState(false);

  if (minimal) {
    return (
      <footer className={cn("py-3 text-center text-xs text-muted-foreground border-t", className)}>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Link to="/terms" className="hover:text-foreground transition-colors">
            Termos
          </Link>
          <span className="opacity-50">•</span>
          <Link to="/privacy" className="hover:text-foreground transition-colors">
            Privacidade
          </Link>
          <span className="opacity-50">•</span>
          <Link to="/cookies" className="hover:text-foreground transition-colors">
            Cookies
          </Link>
          <span className="opacity-50">|</span>
          <span>© {currentYear} Arkheion Corp</span>
        </div>
      </footer>
    );
  }

  // Footer compacto com expansão
  return (
    <footer className={cn("border-t bg-card/30", className)}>
      {/* Barra compacta sempre visível */}
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <TikTrendIcon size={18} />
              <span className="font-medium hidden sm:inline">TikTrend</span>
            </div>
            <span className="hidden md:inline">© {currentYear} Arkheion Corp</span>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {/* Links rápidos sempre visíveis */}
            <div className="hidden sm:flex items-center gap-3 text-muted-foreground">
              <Link to="/terms" className="hover:text-foreground transition-colors">
                Termos
              </Link>
              <Link to="/privacy" className="hover:text-foreground transition-colors">
                Privacidade
              </Link>
              <a href="mailto:suporte@arkheioncorp.com" className="hover:text-foreground transition-colors">
                Suporte
              </a>
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-7 px-2 text-xs gap-1"
            >
              {isExpanded ? "Menos" : "Mais"}
              <ChevronUp className={cn("h-3 w-3 transition-transform", !isExpanded && "rotate-180")} />
            </Button>
          </div>
        </div>
      </div>

      {/* Seção expandida */}
      <div className={cn(
        "overflow-hidden transition-all duration-300 ease-in-out",
        isExpanded ? "max-h-80 opacity-100" : "max-h-0 opacity-0"
      )}>
        <div className="container mx-auto px-4 py-4 border-t border-border/50">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
            {/* Brand */}
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-2 mb-2">
                <TikTrendIcon size={24} />
                <span className="font-bold bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary bg-clip-text text-transparent">
                  TikTrend Finder
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Encontre os produtos mais virais do TikTok e aumente suas vendas.
              </p>
            </div>

            {/* Legal */}
            <div>
              <h4 className="font-semibold text-xs uppercase tracking-wider mb-2 text-muted-foreground">Legal</h4>
              <ul className="space-y-1.5 text-xs">
                <li>
                  <Link to="/terms" className="text-muted-foreground hover:text-foreground transition-colors">
                    Termos de Uso
                  </Link>
                </li>
                <li>
                  <Link to="/privacy" className="text-muted-foreground hover:text-foreground transition-colors">
                    Privacidade
                  </Link>
                </li>
                <li>
                  <Link to="/cookies" className="text-muted-foreground hover:text-foreground transition-colors">
                    Cookies
                  </Link>
                </li>
                <li>
                  <Link to="/acceptable-use" className="text-muted-foreground hover:text-foreground transition-colors">
                    Uso Aceitável
                  </Link>
                </li>
              </ul>
            </div>

            {/* Suporte */}
            <div>
              <h4 className="font-semibold text-xs uppercase tracking-wider mb-2 text-muted-foreground">Suporte</h4>
              <ul className="space-y-1.5 text-xs">
                <li>
                  <a href="mailto:suporte@arkheioncorp.com" className="text-muted-foreground hover:text-foreground transition-colors">
                    suporte@arkheioncorp.com
                  </a>
                </li>
                <li>
                  <Link to="/admin/docs" className="text-muted-foreground hover:text-foreground transition-colors">
                    Documentação API
                  </Link>
                </li>
                <li>
                  <Link to="/admin/metrics" className="text-muted-foreground hover:text-foreground transition-colors">
                    Status do Sistema
                  </Link>
                </li>
              </ul>
            </div>

            {/* Segurança */}
            <div>
              <h4 className="font-semibold text-xs uppercase tracking-wider mb-2 text-muted-foreground">Segurança</h4>
              <ul className="space-y-1.5 text-xs">
                <li>
                  <a href="mailto:security@arkheioncorp.com" className="text-muted-foreground hover:text-foreground transition-colors">
                    Reportar Vulnerabilidade
                  </a>
                </li>
                <li>
                  <a href="mailto:dpo@arkheioncorp.com" className="text-muted-foreground hover:text-foreground transition-colors">
                    Encarregado (DPO)
                  </a>
                </li>
                <li>
                  <a href="mailto:privacidade@arkheioncorp.com" className="text-muted-foreground hover:text-foreground transition-colors">
                    Solicitações LGPD
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="mt-4 pt-3 border-t border-border/30 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <p>© {currentYear} TikTrend / Arkheion Corp. Todos os direitos reservados.</p>
            <div className="flex items-center gap-3">
              <span>🇧🇷 Brasil</span>
              <span>🔒 LGPD</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
