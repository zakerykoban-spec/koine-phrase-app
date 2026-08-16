export type CardMeta = Record<string, unknown>

export interface PhraseCard {
  id: string
  deckId: string
  deckLabel: string
  koine: string
  english: string
  tag?: string
  audio?: string
  image?: string
  meta?: CardMeta
}

export interface PhraseDeck {
  id: string
  filename: string
  label: string
  cards: PhraseCard[]
}

export interface StudySettings {
  showEnglishAid: boolean
  flashcardMode: boolean
  autoHide: boolean
  showParsing: boolean
  repeatAfter: number
}

export interface StudySession {
  queue: string[]
  total: number
  correct: string[]
  incorrect: string[]
  missedOnce: string[]
  repeatEvents: number
  sourceIds: string[]
}

export interface SessionSummary {
  total: number
  firstPassCorrect: number
  missed: number
  repeatEvents: number
  missedIds: string[]
  sourceIds: string[]
}
