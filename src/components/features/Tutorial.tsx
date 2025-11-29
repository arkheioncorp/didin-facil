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
    {
      target: 'body',
      content: (
        <div>
          <h2 className="text-lg font-bold mb-2">Bem-vindo ao TikTrend Finder!</h2>
          <p>Vamos fazer um tour rápido para você conhecer todas as funcionalidades da plataforma.</p>
        </div>
      ),
      placement: 'center',
    },
    {
      target: '[data-testid="nav-dashboard"]',
      content: (
        <div>
          <h3 className="font-bold">Dashboard</h3>
          <p>Aqui você tem uma visão geral das tendências e estatísticas importantes.</p>
        </div>
      ),
      placement: 'right',
    },
    {
      target: '[data-testid="nav-search"]',
      content: (
        <div>
          <h3 className="font-bold">Buscar</h3>
          <p>Realize buscas avançadas por produtos no TikTok Shop.</p>
        </div>
      ),
      placement: 'right',
    },
    {
      target: '[data-testid="nav-products"]',
      content: (
        <div>
          <h3 className="font-bold">Produtos</h3>
          <p>Gerencie e visualize os produtos que você encontrou.</p>
        </div>
      ),
      placement: 'right',
    },
    {
      target: '[data-testid="nav-favorites"]',
      content: (
        <div>
          <h3 className="font-bold">Favoritos</h3>
          <p>Acesse rapidamente os produtos que você salvou.</p>
        </div>
      ),
      placement: 'right',
    },
    {
      target: '[data-testid="nav-copy"]',
      content: (
        <div>
          <h3 className="font-bold">Copy AI</h3>
          <p>Crie textos persuasivos para seus anúncios usando nossa Inteligência Artificial.</p>
        </div>
      ),
      placement: 'right',
    },
    {
      target: '[data-testid="nav-settings"]',
      content: (
        <div>
          <h3 className="font-bold">Configurações</h3>
          <p>Ajuste as preferências da aplicação e do seu perfil.</p>
        </div>
      ),
      placement: 'right',
    },
    {
      target: '[data-testid="search-input"]',
      content: (
        <div>
          <h3 className="font-bold">Busca Rápida</h3>
          <p>Use este campo para encontrar produtos rapidamente em qualquer tela.</p>
        </div>
      ),
      placement: 'bottom',
    },
  ];

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      showProgress
      showSkipButton
      callback={handleJoyrideCallback}
      styles={{
        options: {
          zIndex: 10000,
          primaryColor: '#000',
          textColor: '#333',
          backgroundColor: '#fff',
        },
        buttonNext: {
            backgroundColor: theme === 'dark' ? '#fff' : '#000',
            color: theme === 'dark' ? '#000' : '#fff',
        },
        buttonBack: {
            color: theme === 'dark' ? '#fff' : '#000',
        }
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
