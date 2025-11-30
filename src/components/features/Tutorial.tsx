import { useState, useEffect } from 'react';
import Joyride, { CallBackProps, STATUS, Step } from 'react-joyride';
import { useUserStore } from '@/stores';

export const Tutorial = () => {
  const { theme } = useUserStore();
  const [run, setRun] = useState(false);

  useEffect(() => {
    const tutorialCompleted = localStorage.getItem('tutorial_completed');
    if (!tutorialCompleted) {
      setRun(true);
    }

    const handleRestart = () => {
      setRun(true);
    };

    window.addEventListener('restart_tutorial', handleRestart);

    return () => {
      window.removeEventListener('restart_tutorial', handleRestart);
    };
  }, []);

  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status } = data;
    const finishedStatuses: string[] = [STATUS.FINISHED, STATUS.SKIPPED];

    if (finishedStatuses.includes(status)) {
      setRun(false);
      localStorage.setItem('tutorial_completed', 'true');
    }
  };

  const steps: Step[] = [
    // ═══════════════════════════════════════════════════════════════════
    // 🎯 ONBOARDING - Boas-vindas e modelo de negócio
    // ═══════════════════════════════════════════════════════════════════
    {
      target: 'body',
      content: (
        <div>
          <h2 className="text-lg font-bold mb-2">🚀 Bem-vindo ao TikTrend Finder!</h2>
          <p className="mb-2">Sua plataforma completa para encontrar produtos vencedores e automatizar suas vendas.</p>
          <p className="text-sm text-muted-foreground">Este tour vai te mostrar todas as funcionalidades em ~2 minutos.</p>
        </div>
      ),
      placement: 'center',
      disableBeacon: true,
    },
    {
      target: '[data-testid="user-menu"]',
      content: (
        <div>
          <h3 className="font-bold mb-2">💳 Licença & Créditos</h3>
          <p className="mb-2">Seu acesso funciona assim:</p>
          <ul className="text-sm space-y-1 mb-2">
            <li>• <strong>Licença Vitalícia:</strong> Buscas ilimitadas para sempre</li>
            <li>• <strong>Créditos IA:</strong> Para gerar copies e análises</li>
          </ul>
          <p className="text-xs text-muted-foreground">Clique no seu perfil para ver saldo e comprar créditos.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },

    // ═══════════════════════════════════════════════════════════════════
    // 🔍 CORE - Busca e gestão de produtos
    // ═══════════════════════════════════════════════════════════════════
    {
      target: '[data-testid="nav-dashboard"]',
      content: (
        <div>
          <h3 className="font-bold">📊 Dashboard</h3>
          <p>Visão geral das tendências, métricas de performance e insights do mercado.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-search"]',
      content: (
        <div>
          <h3 className="font-bold">🔍 Buscar Produtos</h3>
          <p className="mb-2">O coração da plataforma! Encontre produtos vencedores no TikTok Shop com filtros avançados.</p>
          <p className="text-sm text-muted-foreground">Buscas ilimitadas com sua licença vitalícia.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-products"]',
      content: (
        <div>
          <h3 className="font-bold">📦 Produtos</h3>
          <p>Gerencie todos os produtos que você encontrou. Organize, compare e exporte para planilhas.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-favorites"]',
      content: (
        <div>
          <h3 className="font-bold">⭐ Favoritos</h3>
          <p>Salve os melhores produtos aqui para acessar rapidamente depois.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="search-input"]',
      content: (
        <div>
          <h3 className="font-bold">⚡ Busca Rápida</h3>
          <p>Encontre qualquer produto instantaneamente de qualquer tela.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },

    // ═══════════════════════════════════════════════════════════════════
    // 🤖 INTELIGÊNCIA ARTIFICIAL - Copy AI + Sistema de Créditos
    // ═══════════════════════════════════════════════════════════════════
    {
      target: '[data-testid="nav-copy"]',
      content: (
        <div>
          <h3 className="font-bold">🤖 Copy AI</h3>
          <p className="mb-2">Crie textos persuasivos para anúncios usando IA avançada.</p>
          <div className="bg-muted p-2 rounded text-sm mt-2">
            <p className="font-medium mb-1">💰 Consumo de Créditos:</p>
            <ul className="space-y-0.5">
              <li>• Copy simples: <strong>1 crédito</strong></li>
              <li>• Análise de tendência: <strong>2 créditos</strong></li>
              <li>• Lote de copies: <strong>5 créditos</strong></li>
            </ul>
          </div>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },

    // ═══════════════════════════════════════════════════════════════════
    // 📱 SOCIAL SUITE - Redes Sociais
    // ═══════════════════════════════════════════════════════════════════
    {
      target: '[data-testid="nav-social"]',
      content: (
        <div>
          <h3 className="font-bold">📱 Social Hub</h3>
          <p className="mb-2">Central de gerenciamento de todas as suas redes sociais em um só lugar.</p>
          <p className="text-sm text-muted-foreground">Conecte Instagram, TikTok e YouTube.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-instagram"]',
      content: (
        <div>
          <h3 className="font-bold">📸 Instagram</h3>
          <p>Gerencie posts, stories e analise métricas do seu perfil comercial.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-tiktok"]',
      content: (
        <div>
          <h3 className="font-bold">🎵 TikTok</h3>
          <p>Acompanhe tendências, agende vídeos e monitore performance dos seus conteúdos.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-youtube"]',
      content: (
        <div>
          <h3 className="font-bold">▶️ YouTube</h3>
          <p>Gerencie seu canal, agende uploads e acompanhe analytics detalhados.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },

    // ═══════════════════════════════════════════════════════════════════
    // ⚡ AUTOMAÇÃO - WhatsApp, Chatbot, Agendador, Seller Bot
    // ═══════════════════════════════════════════════════════════════════
    {
      target: '[data-testid="nav-whatsapp"]',
      content: (
        <div>
          <h3 className="font-bold">💬 WhatsApp Business</h3>
          <p>Automatize atendimento, envie mensagens em massa e gerencie conversas.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-chatbot"]',
      content: (
        <div>
          <h3 className="font-bold">🤖 Chatbot</h3>
          <p>Configure respostas automáticas inteligentes para atender clientes 24/7.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-scheduler"]',
      content: (
        <div>
          <h3 className="font-bold">📅 Agendador</h3>
          <p>Programe posts e ações automáticas para todas as suas redes sociais.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-seller-bot"]',
      content: (
        <div>
          <h3 className="font-bold">🏆 Seller Bot <span className="text-xs bg-gradient-to-r from-yellow-500 to-orange-500 text-white px-1.5 py-0.5 rounded ml-1">PREMIUM</span></h3>
          <p className="mb-2">Automação avançada para vendedores do TikTok Shop.</p>
          <ul className="text-sm space-y-0.5">
            <li>• Publicar produtos automaticamente</li>
            <li>• Responder mensagens com IA</li>
            <li>• Gerenciar pedidos</li>
          </ul>
          <p className="text-xs text-muted-foreground mt-2">Disponível no plano Premium.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },

    // ═══════════════════════════════════════════════════════════════════
    // 📈 CRM & VENDAS - Pipeline e gestão de leads
    // ═══════════════════════════════════════════════════════════════════
    {
      target: '[data-testid="nav-crm"]',
      content: (
        <div>
          <h3 className="font-bold">📈 CRM Dashboard</h3>
          <p>Visão completa das suas vendas, leads e métricas de conversão.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: '[data-testid="nav-pipeline"]',
      content: (
        <div>
          <h3 className="font-bold">🎯 Pipeline de Vendas</h3>
          <p>Gerencie leads em estilo Kanban. Arraste e solte para atualizar status.</p>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },

    // ═══════════════════════════════════════════════════════════════════
    // ⚙️ CONFIGURAÇÕES - Finalização
    // ═══════════════════════════════════════════════════════════════════
    {
      target: '[data-testid="nav-settings"]',
      content: (
        <div>
          <h3 className="font-bold">⚙️ Configurações</h3>
          <p className="mb-2">Personalize a plataforma do seu jeito:</p>
          <ul className="text-sm space-y-0.5">
            <li>• Tema claro/escuro</li>
            <li>• Integrações e APIs</li>
            <li>• Preferências de notificação</li>
          </ul>
        </div>
      ),
      placement: 'auto',
      disableBeacon: true,
    },
    {
      target: 'body',
      content: (
        <div>
          <h2 className="text-lg font-bold mb-2">🎉 Tudo pronto!</h2>
          <p className="mb-2">Você conhece todas as funcionalidades do TikTrend Finder.</p>
          <div className="bg-muted p-3 rounded text-sm">
            <p className="font-medium mb-1">💡 Dica:</p>
            <p>Comece fazendo uma busca de produtos e depois use a Copy AI para criar anúncios incríveis!</p>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Você pode reiniciar este tutorial em Configurações.</p>
        </div>
      ),
      placement: 'center',
      disableBeacon: true,
    },
  ];

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      showProgress
      showSkipButton
      scrollToFirstStep
      scrollOffset={100}
      disableScrolling={false}
      callback={handleJoyrideCallback}
      floaterProps={{
        disableAnimation: false,
        hideArrow: false,
        offset: 15,
        styles: {
          floater: {
            filter: 'drop-shadow(0 4px 20px rgba(0, 0, 0, 0.3))',
          },
        },
      }}
      styles={{
        options: {
          zIndex: 10000,
          primaryColor: '#000',
          textColor: theme === 'dark' ? '#fff' : '#333',
          backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
          arrowColor: theme === 'dark' ? '#1f2937' : '#fff',
          overlayColor: 'rgba(0, 0, 0, 0.6)',
          width: 340,
        },
        tooltip: {
          borderRadius: 12,
          padding: 16,
          maxWidth: '90vw',
        },
        tooltipContainer: {
          textAlign: 'left',
        },
        tooltipContent: {
          padding: '8px 0',
        },
        buttonNext: {
          backgroundColor: theme === 'dark' ? '#fff' : '#000',
          color: theme === 'dark' ? '#000' : '#fff',
          borderRadius: 8,
          padding: '8px 16px',
        },
        buttonBack: {
          color: theme === 'dark' ? '#fff' : '#000',
          marginRight: 8,
        },
        buttonSkip: {
          color: theme === 'dark' ? '#9ca3af' : '#6b7280',
        },
        spotlight: {
          borderRadius: 8,
        },
      }}
      locale={{
        back: 'Voltar',
        close: 'Fechar',
        last: 'Finalizar',
        next: 'Próximo',
        skip: 'Pular',
      }}
    />
  );
};
