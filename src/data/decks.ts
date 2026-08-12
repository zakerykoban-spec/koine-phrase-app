import type { CardMeta, PhraseCard, PhraseDeck } from '../types'

type RawCard = {
  id?: unknown
  koine?: unknown
  english?: unknown
  tag?: unknown
  audio?: unknown
  image?: unknown
  meta?: unknown
}

function clean(value: unknown): string {
  return typeof value === 'string' ? value.trim() : value == null ? '' : String(value).trim()
}

function labelFromFilename(filename: string): string {
  const stem = filename.replace(/\.json$/i, '')

  if (/^400_friends/i.test(stem)) return '400 Friends — Source Faithful'
  if (/^conversational_koine_phrases$/i.test(stem)) return 'Conversational Koine Phrases'

  const didache = stem.match(/^didache_ch0?(\d+)_(lexical|usage)(?:_deck)?(?:_parsed)?$/i)
  if (didache) {
    const [, chapter, kind] = didache
    return `Didache Ch. ${Number(chapter)} — ${kind[0].toUpperCase()}${kind.slice(1).toLowerCase()}`
  }

  return stem
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function normalizeDeck(path: string, raw: unknown): PhraseDeck | null {
  if (!Array.isArray(raw)) return null

  const filename = path.split('/').pop() ?? path
  const id = filename.replace(/\.json$/i, '')
  const label = labelFromFilename(filename)

  const cards = raw.flatMap((entry, index): PhraseCard[] => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return []
    const source = entry as RawCard
    const koine = clean(source.koine)
    const english = clean(source.english)
    if (!koine && !english) return []

    const baseId = clean(source.id) || String(index + 1).padStart(4, '0')
    const meta = source.meta && typeof source.meta === 'object' && !Array.isArray(source.meta)
      ? (source.meta as CardMeta)
      : undefined

    return [{
      id: `${id}:${baseId}`,
      deckId: id,
      deckLabel: label,
      koine,
      english,
      tag: clean(source.tag) || undefined,
      audio: clean(source.audio) || undefined,
      image: clean(source.image) || undefined,
      meta,
    }]
  })

  return { id, filename, label, cards }
}

const modules = import.meta.glob('/decks/*.json', { eager: true }) as Record<string, { default: unknown }>

export const decks: PhraseDeck[] = Object.entries(modules)
  .map(([path, module]) => normalizeDeck(path, module.default))
  .filter((deck): deck is PhraseDeck => deck !== null)
  .sort((a, b) => a.label.localeCompare(b.label, 'en'))

export const allCards = decks.flatMap((deck) => deck.cards)
