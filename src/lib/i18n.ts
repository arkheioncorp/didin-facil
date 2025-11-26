import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    debug: true,
    fallbackLng: 'pt',
    interpolation: {
      escapeValue: false,
    },
    resources: {
      en: {
        translation: {
          welcome: "Welcome to TikTrend Finder",
          search: "Search",
          products: "Products",
          favorites: "Favorites",
          settings: "Settings"
        }
      },
      pt: {
        translation: {
          welcome: "Bem-vindo ao TikTrend Finder",
          search: "Buscar",
          products: "Produtos",
          favorites: "Favoritos",
          settings: "Configurações"
        }
      }
    }
  });

export default i18n;
