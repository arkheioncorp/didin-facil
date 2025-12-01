import * as React from "react";
import { Link } from "react-router-dom";
import { TikTrendIcon } from "@/components/icons";
import { cn } from "@/lib/utils";

interface FooterProps {
  className?: string;
  minimal?: boolean;
}

export const Footer: React.FC<FooterProps> = ({ className, minimal = false }) => {
  const currentYear = new Date().getFullYear();

  if (minimal) {
    return (
      <footer className={cn("py-4 text-center text-sm text-muted-foreground", className)}>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link to="/terms" className="hover:text-foreground transition-colors">
            Termos de Uso
          </Link>
          <span className="hidden sm:inline">•</span>
          <Link to="/privacy" className="hover:text-foreground transition-colors">
            Privacidade
          </Link>
          <span className="hidden sm:inline">•</span>
          <Link to="/cookies" className="hover:text-foreground transition-colors">
            Cookies
          </Link>
        </div>
        <p className="mt-2">
          © {currentYear} TikTrend / Arkheion Corp. Todos os direitos reservados.
        </p>
      </footer>
    );
  }

  return (
    <footer className={cn("border-t bg-card/50 backdrop-blur-sm", className)}>
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <TikTrendIcon size={32} />
              <span className="font-bold text-lg bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary bg-clip-text text-transparent">
                TikTrend Finder
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Encontre os produtos mais virais do TikTok e aumente suas vendas com análises inteligentes.
            </p>
          </div>

          {/* Links Legais */}
          <div>
            <h4 className="font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link 
                  to="/terms" 
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Termos de Uso
                </Link>
              </li>
              <li>
                <Link 
                  to="/privacy" 
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Política de Privacidade
                </Link>
              </li>
              <li>
                <Link 
                  to="/cookies" 
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Política de Cookies
                </Link>
              </li>
              <li>
                <Link 
                  to="/acceptable-use" 
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Uso Aceitável
                </Link>
              </li>
            </ul>
          </div>

          {/* Suporte */}
          <div>
            <h4 className="font-semibold mb-4">Suporte</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a 
                  href="mailto:suporte@arkheioncorp.com" 
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  suporte@arkheioncorp.com
                </a>
              </li>
              <li>
                <a 
                  href="https://docs.tiktrend.com.br" 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Documentação
                </a>
              </li>
              <li>
                <a 
                  href="https://status.tiktrend.com.br" 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Status do Sistema
                </a>
              </li>
            </ul>
          </div>

          {/* Segurança */}
          <div>
            <h4 className="font-semibold mb-4">Segurança</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a 
                  href="mailto:security@arkheioncorp.com" 
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Reportar Vulnerabilidade
                </a>
              </li>
              <li>
                <a 
                  href="mailto:dpo@arkheioncorp.com" 
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Encarregado de Dados (DPO)
                </a>
              </li>
              <li>
                <a 
                  href="mailto:privacidade@arkheioncorp.com" 
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Solicitações LGPD
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-border/50">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
            <p>
              © {currentYear} TikTrend / Arkheion Corp. Todos os direitos reservados.
            </p>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                🇧🇷 Feito no Brasil
              </span>
              <span className="hidden sm:inline">•</span>
              <span className="flex items-center gap-1">
                🔒 LGPD Compliant
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
