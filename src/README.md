# ⚛️ Frontend do Didin Fácil

Este diretório contém o código fonte da interface do usuário, construída com React, TypeScript e Vite.

## 🏗️ Estrutura

- **`components/`**: Componentes reutilizáveis da UI (baseados em Radix UI / Shadcn).
- **`pages/`**: Páginas da aplicação (Roteamento).
- **`hooks/`**: Custom React Hooks.
- **`stores/`**: Gerenciamento de estado (Zustand).
- **`services/`**: Integração com API e serviços externos.
- **`lib/`**: Utilitários e configurações.
- **`styles/`**: Estilos globais e Tailwind CSS.
- **`locales/`**: Arquivos de internacionalização (i18n).

## 🚀 Como Rodar

### Pré-requisitos

- Node.js 18+
- NPM ou Yarn

### Instalação

1. Instale as dependências:

   ```bash
   npm install
   ```

2. Inicie o servidor de desenvolvimento:

   ```bash
   npm run dev
   ```

3. Para rodar como aplicação Desktop (Tauri):

   ```bash
   npm run tauri:dev
   ```

## 🧪 Testes

- **Unitários:** `npm run test`
- **E2E:** `npm run test:e2e`
