import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'

const savedLang = localStorage.getItem('lang') || navigator.language.startsWith('zh') ? 'zh' : 'en'

const i18n = createI18n({
  legacy: false,
  locale: savedLang,
  fallbackLocale: 'en',
  messages: { zh, en },
})

export function setLanguage(lang: string) {
  ; (i18n.global.locale as any).value = lang
  localStorage.setItem('lang', lang)
  document.documentElement.setAttribute('lang', lang)
}

export default i18n
