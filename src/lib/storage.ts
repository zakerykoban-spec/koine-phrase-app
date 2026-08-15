import type { PhraseDeck, StudySettings } from '../types'

const KEYS = {
  selectedDecks: 'koine.v2.selectedDecks',
  favorites: 'koine.v2.favorites',
  settings: 'koine.v2.settings',
  lastCard: 'koine.v2.lastCard',
  importedDecks: 'koine.v2.importedDecks',
} as const

export const DEFAULT_SETTINGS: StudySettings = {
  flashcardMode: true,
  autoHide: true,
  showParsing: true,
  repeatAfter: 3,
}

function readJson<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function writeJson(key: string, value: unknown) {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Storage can be unavailable in private browsing or restricted webviews.
  }
}

function isPhraseDeck(value: unknown): value is PhraseDeck {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  const source = value as Partial<PhraseDeck>
  return typeof source.id === 'string'
    && typeof source.filename === 'string'
    && typeof source.label === 'string'
    && Array.isArray(source.cards)
}

export function loadSelectedDecks(): string[] {
  const value = readJson<unknown>(KEYS.selectedDecks, [])
  return Array.isArray(value) ? value.map(String) : []
}

export function saveSelectedDecks(deckIds: string[]) {
  writeJson(KEYS.selectedDecks, deckIds)
}

export function loadFavorites(): string[] {
  const value = readJson<unknown>(KEYS.favorites, [])
  return Array.isArray(value) ? value.map(String) : []
}

export function saveFavorites(cardIds: string[]) {
  writeJson(KEYS.favorites, cardIds)
}

export function loadSettings(): StudySettings {
  const value = readJson<Partial<StudySettings>>(KEYS.settings, {})
  return {
    ...DEFAULT_SETTINGS,
    ...value,
    repeatAfter: Math.max(0, Math.min(8, Number(value.repeatAfter ?? DEFAULT_SETTINGS.repeatAfter))),
  }
}

export function saveSettings(settings: StudySettings) {
  writeJson(KEYS.settings, settings)
}

export function loadImportedDecks(): PhraseDeck[] {
  const value = readJson<unknown>(KEYS.importedDecks, [])
  return Array.isArray(value) ? value.filter(isPhraseDeck) : []
}

export function saveImportedDecks(decks: PhraseDeck[]) {
  writeJson(KEYS.importedDecks, decks)
}

export function loadLastCard(): string | null {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage.getItem(KEYS.lastCard)
  } catch {
    return null
  }
}

export function saveLastCard(cardId: string | null) {
  if (typeof window === 'undefined') return
  try {
    if (cardId) window.localStorage.setItem(KEYS.lastCard, cardId)
    else window.localStorage.removeItem(KEYS.lastCard)
  } catch {
    // Ignore storage failures.
  }
}
