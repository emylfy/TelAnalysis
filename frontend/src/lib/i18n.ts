import i18n from "i18next"
import { initReactI18next } from "react-i18next"

// UI-chrome strings only. Python-composed sentences (hero prose, highlight
// labels) arrive already localized from the API via ?lang=.
const resources = {
  ru: {
    translation: {
      messages: "Сообщений",
      participants: "Участников",
      daysActive: "Дней активно",
      media: "Медиа",
      highlights: "Заметное",
      howOften: "Как часто пишут",
      type_personal_chat: "Личный чат",
      type_private_group: "Группа",
      type_private_supergroup: "Группа",
      type_public_supergroup: "Группа",
      type_private_channel: "Канал",
      type_public_channel: "Канал",
      type_bot_chat: "Бот",
      type_saved_messages: "Избранное",
      type_multichat: "Объединённый",
    },
  },
  en: {
    translation: {
      messages: "Messages",
      participants: "Participants",
      daysActive: "Days active",
      media: "Media",
      highlights: "Highlights",
      howOften: "How often",
      type_personal_chat: "Personal chat",
      type_private_group: "Group",
      type_private_supergroup: "Group",
      type_public_supergroup: "Group",
      type_private_channel: "Channel",
      type_public_channel: "Channel",
      type_bot_chat: "Bot",
      type_saved_messages: "Saved Messages",
      type_multichat: "Combined",
    },
  },
}

i18n.use(initReactI18next).init({
  resources,
  lng: "ru",
  fallbackLng: "ru",
  interpolation: { escapeValue: false },
})

export function chatTypeLabel(t: string): string {
  const key = `type_${t}`
  const v = i18n.t(key)
  return v === key ? t : v
}

export function fmtInt(n: number, lang: string): string {
  return new Intl.NumberFormat(lang === "ru" ? "ru-RU" : "en-US").format(n)
}

export default i18n
