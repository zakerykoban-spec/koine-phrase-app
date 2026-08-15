import type { CardMeta, PhraseCard, PhraseDeck } from '../types'

type RawCard = Record<string, unknown>

const GREEK_KEYS = ['koine', 'greek', 'grc', 'phrase', 'front']
const ENGLISH_KEYS = ['english', 'translation', 'gloss', 'meaning', 'back']
const TAG_KEYS = ['tag', 'category', 'topic']
const AUDIO_KEYS = ['audio', 'audiofile', 'audio_file']
const IMAGE_KEYS = ['image', 'imagefile', 'image_file']

function clean(value: unknown): string {
  return typeof value === 'string' ? value.trim() : value == null ? '' : String(value).trim()
}

function normalizeKey(value: string): string {
  return value.trim().toLocaleLowerCase().replace(/[\s_-]+/g, '')
}

function findKey(record: RawCard, aliases: string[]): string | undefined {
  const wanted = new Set(aliases.map(normalizeKey))
  return Object.keys(record).find((key) => wanted.has(normalizeKey(key)))
}

function pick(record: RawCard, aliases: string[]): string {
  const key = findKey(record, aliases)
  return key ? clean(record[key]) : ''
}

function titleFromFilename(filename: string): string {
  const stem = filename.replace(/\.[^.]+$/, '')
  return stem
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase()) || 'Imported Deck'
}

function slugify(value: string): string {
  const slug = value
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return slug || 'deck'
}

function makeDeckId(label: string): string {
  const stamp = Date.now().toString(36)
  const random = Math.random().toString(36).slice(2, 8)
  return `imported-${slugify(label)}-${stamp}-${random}`
}

function parseDelimited(text: string, delimiter: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let quoted = false

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index]
    const next = text[index + 1]

    if (char === '"') {
      if (quoted && next === '"') {
        field += '"'
        index += 1
      } else {
        quoted = !quoted
      }
      continue
    }

    if (!quoted && char === delimiter) {
      row.push(field.trim())
      field = ''
      continue
    }

    if (!quoted && (char === '\n' || char === '\r')) {
      if (char === '\r' && next === '\n') index += 1
      row.push(field.trim())
      if (row.some((value) => value.length > 0)) rows.push(row)
      row = []
      field = ''
      continue
    }

    field += char
  }

  row.push(field.trim())
  if (row.some((value) => value.length > 0)) rows.push(row)
  return rows
}

function detectDelimiter(text: string, extension: string): string {
  if (extension === 'csv') return ','
  if (extension === 'tsv') return '\t'

  const firstNonEmptyLine = text.split(/\r?\n/).find((line) => line.trim()) ?? ''
  const candidates = ['\t', '|', ',', ';']
  const best = candidates
    .map((delimiter) => ({ delimiter, count: firstNonEmptyLine.split(delimiter).length - 1 }))
    .sort((a, b) => b.count - a.count)[0]

  if (!best || best.count < 1) {
    throw new Error('TXT decks need at least two columns separated by a tab, pipe, comma, or semicolon.')
  }
  return best.delimiter
}

function hasHeader(row: string[]): boolean {
  const recognized = new Set([
    ...GREEK_KEYS,
    ...ENGLISH_KEYS,
    ...TAG_KEYS,
    ...AUDIO_KEYS,
    ...IMAGE_KEYS,
    'id',
  ].map(normalizeKey))
  return row.some((value) => recognized.has(normalizeKey(value)))
}

function rowsToRecords(rows: string[][]): RawCard[] {
  if (rows.length === 0) return []

  if (!hasHeader(rows[0])) {
    return rows.map((row, index) => ({
      id: String(index + 1),
      koine: row[0] ?? '',
      english: row[1] ?? '',
      tag: row[2] ?? '',
    }))
  }

  const headers = rows[0].map((header, index) => header.trim() || `column${index + 1}`)
  return rows.slice(1).map((row) => Object.fromEntries(headers.map((header, index) => [header, row[index] ?? ''])))
}

function normalizeCards(entries: unknown[], deckId: string, deckLabel: string): PhraseCard[] {
  return entries.flatMap((entry, index): PhraseCard[] => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return []
    const source = entry as RawCard
    const koine = pick(source, GREEK_KEYS)
    const english = pick(source, ENGLISH_KEYS)
    if (!koine && !english) return []

    const knownKeys = new Set([
      'id',
      ...GREEK_KEYS,
      ...ENGLISH_KEYS,
      ...TAG_KEYS,
      ...AUDIO_KEYS,
      ...IMAGE_KEYS,
      'meta',
    ].map(normalizeKey))

    const extraMeta = Object.fromEntries(
      Object.entries(source).filter(([key, value]) => !knownKeys.has(normalizeKey(key)) && clean(value)),
    )
    const sourceMeta = source.meta && typeof source.meta === 'object' && !Array.isArray(source.meta)
      ? (source.meta as CardMeta)
      : {}
    const meta = { ...extraMeta, ...sourceMeta }
    const baseId = clean(source.id) || String(index + 1).padStart(4, '0')

    return [{
      id: `${deckId}:${baseId}`,
      deckId,
      deckLabel,
      koine,
      english,
      tag: pick(source, TAG_KEYS) || undefined,
      audio: pick(source, AUDIO_KEYS) || undefined,
      image: pick(source, IMAGE_KEYS) || undefined,
      meta: Object.keys(meta).length > 0 ? meta : undefined,
    }]
  })
}

export async function importPhraseDeck(file: File): Promise<PhraseDeck> {
  const text = (await file.text()).replace(/^\uFEFF/, '')
  if (!text.trim()) throw new Error('This file is empty.')

  const extension = file.name.split('.').pop()?.toLocaleLowerCase() ?? ''
  let label = titleFromFilename(file.name)
  let entries: unknown[]

  if (extension === 'json') {
    let parsed: unknown
    try {
      parsed = JSON.parse(text)
    } catch {
      throw new Error('The JSON file could not be parsed.')
    }

    if (Array.isArray(parsed)) {
      entries = parsed
    } else if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      const source = parsed as Record<string, unknown>
      if (!Array.isArray(source.cards)) throw new Error('JSON decks must be an array of cards or an object with a cards array.')
      entries = source.cards
      label = clean(source.label) || clean(source.name) || clean(source.title) || label
    } else {
      throw new Error('JSON decks must be an array of cards or an object with a cards array.')
    }
  } else if (['csv', 'tsv', 'txt'].includes(extension)) {
    const delimiter = detectDelimiter(text, extension)
    entries = rowsToRecords(parseDelimited(text, delimiter))
  } else {
    throw new Error('Use a .json, .csv, .tsv, or .txt deck file.')
  }

  const id = makeDeckId(label)
  const cards = normalizeCards(entries, id, label)
  if (cards.length === 0) {
    throw new Error('No study cards were found. Include Greek/Koine and English/Translation columns.')
  }

  return {
    id,
    filename: file.name,
    label,
    cards,
  }
}
