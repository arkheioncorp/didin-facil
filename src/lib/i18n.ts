import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import ptBR from '@/locales/pt-BR.json';
import en from '@/locales/en.json';
import es from '@/locales/es.json';

// Supported languages configuration
export const SUPPORTED_LANGUAGES = [
  { code: 'pt-BR', name: 'Português (Brasil)', flag: '🇧🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
] as const;

export type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number]['code'];

// Helper to get saved language from localStorage
const getSavedLanguage = (): string | null => {
  try {
    const settings = localStorage.getItem('app-settings');
    if (settings) {
      const parsed = JSON.parse(settings);
      return parsed.state?.language || null;
    }
  } catch {
    // Ignore parse errors
  }
  return null;
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    // Debug mode only in development
    debug: import.meta.env.DEV,
    
    // Fallback language
    fallbackLng: 'pt-BR',
    
    // Default language (try saved, then detect, then fallback)
    lng: getSavedLanguage() || undefined,
    
    // Supported languages
    supportedLngs: ['pt-BR', 'en', 'es'],
    
    // Namespace configuration
    defaultNS: 'translation',
    ns: ['translation'],
    
    // Interpolation settings
    interpolation: {
      escapeValue: false, // React already escapes
      formatSeparator: ',',
    },
    
    // Detection order
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      lookupLocalStorage: 'i18nextLng',
      caches: ['localStorage'],
    },
    
    // Resources (translations)
    resources: {
      'pt-BR': {
        translation: ptBR,
      },
      en: {
        translation: en,
      },
      es: {
        translation: es,
      },
    },
    
    // React specific settings
    react: {
      useSuspense: true,
      bindI18n: 'languageChanged',
      bindI18nStore: '',
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'p', 'span'],
    },
  });

// Helper function to change language and persist
export const changeLanguage = async (lang: SupportedLanguage): Promise<void> => {
  await i18n.changeLanguage(lang);
  
  // Also update app-settings in localStorage
  try {
    const settings = localStorage.getItem('app-settings');
    if (settings) {
      const parsed = JSON.parse(settings);
      parsed.state = { ...parsed.state, language: lang };
      localStorage.setItem('app-settings', JSON.stringify(parsed));
    }
  } catch {
    // Ignore errors
  }
};

// Get current language info
export const getCurrentLanguageInfo = () => {
  const currentLang = i18n.language;
  return SUPPORTED_LANGUAGES.find(l => l.code === currentLang) || SUPPORTED_LANGUAGES[0];
};

export default i18n;
